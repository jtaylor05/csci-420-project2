const { ListTablesCommand, DynamoDBClient, PutItemCommand,
        GetItemCommand, ScanCommand, UpdateItemCommand,
        DeleteItemCommand } = require("@aws-sdk/client-dynamodb");
const { marshall, unmarshall } = require("@aws-sdk/util-dynamodb");
const { v4: uuidv4 } = require('uuid');

// comment out the old db config
// const dbConfig = require("../config/config");

const client = new DynamoDBClient({ region: "us-east-1" });
const TABLE_NAME = process.env.DYNAMODB_TABLE || "STUDENTS";; // match whatever you named your table

//const dbConfig = require("../config/config");
// constructor
const Supplier = function (supplier) {
    this.id = supplier.id;
    this.name = supplier.name;
    this.address = supplier.address;
    this.city = supplier.city;
    this.state = supplier.state;
    this.email = supplier.email;
    this.phone = supplier.phone;
};
// connecting on each request so the server will start without a db connection, plus
//   a simple mechanism enabling the app to recover from a momentary missing db connection
// Supplier.dbConnect = () => {
//     const connection = mysql.createConnection({
//         host: dbConfig.APP_DB_HOST,
//         user: dbConfig.APP_DB_USER,
//         password: dbConfig.APP_DB_PASSWORD,
//         database: dbConfig.APP_DB_NAME
//     });
//     connection.connect(error => {
//         if (error) {
//             console.log("Error connecting to Db")
//             throw error;
//         }
//         console.log("Successfully connected to the database.");
//     });
//     return connection;
// }

Supplier.create = (newStudent, result) => {
  (async () => {
    try {
      const item = { ...newStudent, id: uuidv4() };
      await client.send(new PutItemCommand({
        TableName: TABLE_NAME,
        Item: marshall(item, { removeUndefinedValues: true, convertClassInstanceToMap: true })
      }));
      result(null, item);
    } catch (e) {
      result(e, null);
    }
  })();
};

Supplier.getAll = (result) => {
  (async () => {
    try {
      const data = await client.send(new ScanCommand({ TableName: TABLE_NAME }));
      
      // If no items exist, return an empty array rather than throwing
      if (!data.Items || data.Items.length === 0) {
        result(null, []);
        return;
      }

      const students = data.Items.map((item) => unmarshall(item));
      result(null, students);
    } catch (e) {
      result(e, null);
    }
  })();
};

Supplier.findById = (id, result) => {
  (async () => {
    try {
      const data = await client.send(new GetItemCommand({
        TableName: TABLE_NAME,
        Key: marshall({ id })
      }));
      if (!data.Item) {
        result({ kind: "not_found" }, null);
        return;
      }
      result(null, unmarshall(data.Item));
    } catch (e) {
      result(e, null);
    }
  })();
};

Supplier.updateById = (id, student, result) => {
  (async () => {
    try {
      await client.send(new PutItemCommand({
        TableName: TABLE_NAME,
        Item: marshall({ ...student, id }, { removeUndefinedValues: true, convertClassInstanceToMap: true })
      }));
      result(null, { id, ...student });
    } catch (e) {
      result(e, null);
    }
  })();
};

Supplier.remove = (id, result) => {
  (async () => {
    try {
      await client.send(new DeleteItemCommand({
        TableName: TABLE_NAME,
        Key: marshall({ id })
      }));
      result(null, { id });
    } catch (e) {
      result(e, null);
    }
  })();
};

Supplier.removeAll = (result) => {
  (async () => {
    try {
      // DynamoDB has no "DELETE FROM table" equivalent, so we
      // scan for all items first, then delete each one by its key
      const scanData = await client.send(new ScanCommand({ TableName: TABLE_NAME }));

      if (!scanData.Items || scanData.Items.length === 0) {
        console.log("No students to delete");
        result(null, { deleted: 0 });
        return;
      }

      // Delete each item individually using its id
      const deletePromises = scanData.Items.map((item) => {
        const { id } = unmarshall(item);
        return client.send(new DeleteItemCommand({
          TableName: TABLE_NAME,
          Key: marshall({ id })
        }));
      });

      await Promise.all(deletePromises);

      console.log(`deleted ${scanData.Items.length} students`);
      result(null, { deleted: scanData.Items.length });

    } catch (e) {
      console.log("error: ", e);
      result(e, null);
    }
  })();
};

module.exports = Supplier;