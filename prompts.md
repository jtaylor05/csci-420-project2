# WebApp Project — AI Chat Log

A record of prompts and responses used during the WebApp multi-phase AWS project. Organised chronologically by session date.

---

## March 3 — Phase 1 & 2 Overview

### Prompt
> I have supplied a `.docx` file with the specifications for a multi-phase project utilising AWS and cloud tools. Could you read the document and provide a short summary of each phase as well as a bullet point list of key points for the whole project?

### Response

#### Phase 1 – Starting with a Monolith
A pre-built Node.js web application is deployed on a single EC2 instance using a provided CloudFormation template. The instance hosts both the web app and a MySQL database together (a "monolith"). The main task is deploying and testing the template by adding, editing, and deleting student records via the web UI.

#### Phase 2 – Decoupling the Application
This phase separates the database from the web server. MySQL is migrated to a managed Amazon RDS instance placed in private subnets, with credentials stored in AWS Secrets Manager. A new EC2 instance handles only the web application layer, improving security and enabling each layer to scale independently.

#### Phase 3 – High Availability and Scalability
An Application Load Balancer (ALB) spans two Availability Zones, backed by an EC2 Auto Scaling group that scales between 1 and 4 instances based on CPU utilisation (target: 30%). Load testing is performed using a Node.js `loadtest` tool to verify the system scales under pressure.

#### Phase 4 – Migrating to DynamoDB
The data access layer (`supplier.model.js`) is rewritten to use DynamoDB instead of MySQL. The modified app is deployed via a new CloudFormation template with code hosted in an S3 bucket. This demonstrates how the same application can run on both relational and NoSQL datastores.

#### Key Points for the Whole Project
- All infrastructure is managed as code using AWS CloudFormation, with templates updated incrementally across phases.
- AI agents are encouraged — students must save their prompt history as part of the submission.
- Cost awareness is emphasised: the EC2/RDS stack must be deleted when not in use.
- Security improves progressively — credentials move from hardcoded values → environment variables → AWS Secrets Manager, with servers placed in appropriate public/private subnets.
- The project covers a full AWS stack: VPC, EC2, RDS, Secrets Manager, ALB, Auto Scaling, S3, and DynamoDB.
- Students must submit CloudFormation YAMLs, code files, load testing evidence, and a written analysis comparing DynamoDB vs. MySQL.
- Grading rewards prompt quality and critical analysis of AI-generated outputs — including identifying both good and bad solutions.

---

### Prompt
> Can you outline the steps to complete the last part of Phase 1?

### Response

#### Task 3 – Deploy the CloudFormation Stack
1. Open the AWS Management Console and navigate to CloudFormation.
2. Choose **Create stack**.
3. Upload the provided `webapp-phase1.yaml` template.
4. When prompted for an IAM role, select **LabRole**.
5. Complete the stack creation wizard and launch the stack.
6. Wait for the stack status to show `CREATE_COMPLETE`.

#### Task 4 – Test the Deployment
1. In CloudFormation, go to the **Outputs** tab of your newly created stack and find the Public IPv4 address or DNS of the `WebAppPOC` instance.
2. Open a browser and navigate to that address — use `http://`, not `https://`.
3. Confirm the student records web application loads correctly.
4. Test functionality by:
   - Adding at least one new student record
   - Editing an existing record
   - Deleting a record
5. Leave at least one record in the database — it will be needed for the data migration in Phase 2.

#### Before Moving On
- Double-check the `WebAppPOC` EC2 instance is in a **Running** state with 2/2 status checks passed (visible in the EC2 console).
- Remember to delete your stack when you stop working to avoid burning through lab funds.

---

### I do like how the model took to summarizing throughout this tasking. As I instructed, it accurately followed the stage by stage sections. It made it easier to parse the whole work.

### Prompt
> Let us move on to Phase 2. Could you elaborate the steps for Phase 2?

### Response

#### Task 1 – Reconfigure the VPC Network
1. Go to **VPC** in the AWS Console.
2. Create a new private subnet:
   - Name: `Private Subnet 1`, VPC: `WebAppVPC`, AZ: same as your EC2 instance, CIDR: `10.0.2.0/24`
3. Create a private route table named `WebAppPrivateRT` in `WebAppVPC` — confirm it has only one route: `10.0.0.0/16 → local`.
4. Create a second private subnet:
   - Name: `Private Subnet 2`, VPC: `WebAppVPC`, AZ: different from Public Subnet 1, CIDR: `10.0.4.0/24`
5. Associate both private subnets with `WebAppPrivateRT`.

#### Task 2 – Create and Configure the RDS Database
1. In EC2, create a new security group:
   - Name: `WebAppDBSG`, VPC: `WebAppVPC`, Inbound rule: MySQL/Aurora from `10.0.0.0/16`
2. In RDS, create a new database:
   - Engine: MySQL, Free tier template
   - Identifier: `WebAppDB`, Username: `nodeapp`, Password: `wmcc26db`
   - Instance class: `db.t3.micro`, Storage: 20 GiB
   - VPC: `WebAppVPC`, Public access: **No**
   - Security group: `WebAppDBSG` (remove the default)
   - AZ: first in the dropdown, Initial database name: `STUDENTS`
   - Disable Enhanced Monitoring
3. Wait for the database status to show **Available**.
4. Note down the RDS endpoint from the **Connectivity & Security** tab.

#### Task 3 – Set Up Secrets Manager
Open the AWS Learner Lab Console (or CloudShell) and run the following, replacing `<rds-endpoint>`:

```bash
aws secretsmanager create-secret \
    --name Mydbsecret \
    --description "Database secret for web app" \
    --secret-string "{\"user\":\"nodeapp\",\"password\":\"student12\",\"host\":\"<rds-endpoint>\",\"db\":\"STUDENTS\"}"
```

This stores DB credentials securely so the app can retrieve them via the LabRole IAM role.

#### Task 4 – Provision the New Web Server EC2 Instance
1. Launch a new EC2 instance:
   - Name: `WebAppAppServer`, OS: Ubuntu, Type: `t2.micro`
   - Key pair: `vockey`, VPC: `WebAppVPC`, Subnet: `Public Subnet 1`
   - Auto-assign public IP: **Enable**, Security group: `WebAppAPPSG`
   - IAM instance profile: `LabInstanceProfile`
2. In Advanced Details, paste the web server setup script (`WebApp-server-setup.sh`) into the **User Data** field.
3. Launch and wait for the instance to reach **Running** state.

#### Task 5 – Test and Debug the Application
1. Open the public IP of `WebAppAppServer` in a browser using `http://` — it won't work yet, this is expected.
2. To diagnose, connect via EC2 Instance Connect or SSH and run `journalctl -f` while using the app.
3. The issue is likely the password in your secret. Update it in Secrets Manager to match `wmcc26db`:

```bash
aws secretsmanager update-secret --secret-id Mydbsecret \
    --secret-string "{\"user\":\"nodeapp\",\"password\":\"wmcc26db\",\"host\":\"<rds-endpoint>\",\"db\":\"STUDENTS\"}"
```

4. Restart the instance from the EC2 portal to apply changes.
5. The app won't be fully working until the database is migrated — continue to Task 6.

#### Task 6 – Migrate the Database
1. Open the Learner Lab Console.
2. Export data from the original `WebAppPOC` instance (replace `<EC2instancePrivateIP>`):

```bash
mysqldump -h <EC2instancePrivateIP> -u nodeapp -p --database=STUDENTS > data.sql
# Password: student12
```

3. Import it into the RDS database (replace `<RDSEndpoint>`):

```bash
mysql -h <RDSEndpoint> -u nodeapp -p STUDENTS < data.sql
# Password: wmcc26db
```

4. Update your CloudFormation YAML so future deployments automatically create the database schema at startup.
5. Remove the `WebAppPOC` instance from the CloudFormation template as it is no longer needed.

#### Task 7 – Final Test
1. Access the app via the public IP of `WebAppAppServer` using `http://`.
2. Confirm all student records are present and that adding, editing, and deleting records all work correctly.

#### Key Things to Remember
- Always use `http`, not `https`.
- The CloudFormation YAML should be updated to reflect all Phase 2 changes — ideally you should be able to redeploy the entire stack from scratch.
- Delete your stack when you stop working to conserve lab funds.

---

### I think the model should provide a better analysis of best practice on AWS. It does not initially suggest to use something like CloudFormation, which makes a cleaner product and a easier to secure product.

## March 4 — Phase 2 Debugging

### Prompt
> I am having an issue in Task 6. The command is returning the error: `mysqldump: Got error: 2003: Can't connect to MySQL server on '10.0.1.48' (110)` when trying to connect. Do you have any idea why this is?

### Response
This is a classic networking/firewall issue. Most likely causes:

1. **Security Group not allowing MySQL traffic** — verify that `WebAppAPPSG` has an inbound rule for MySQL/Aurora on port 3306 with source `10.0.0.0/16`.

2. **MySQL not bound to the right address** — the Phase 1 user data script should have set `bind-address = 0.0.0.0`. To check, SSH into `WebAppPOC` and run:
   ```bash
   sudo cat /etc/mysql/mysql.conf.d/mysqld.cnf | grep bind-address
   ```
   If it still shows `127.0.0.1`, run the `sed` command manually and restart MySQL with `sudo service mysql restart`.

3. **Running the dump from outside the VPC** — `10.0.1.48` is a private IP, unreachable from outside the VPC. The command must be run from within the VPC (e.g. from the Learner Lab Console or another EC2 instance).

4. **MySQL service isn't running** — SSH into `WebAppPOC` and run `sudo service mysql status`. Start it if needed with `sudo service mysql start`.

**Recommended debugging order:** check MySQL is running → check bind-address → verify security group → confirm you're running the command from within the VPC.

---

### Prompt
> All of that is fine. I am running the command on the Learner Lab. The password is also right because I can connect to MySQL inside the EC2 instance.

### Response
Since you can connect locally inside the EC2 instance but not remotely, the issue is almost certainly **MySQL user permissions**. By default, MySQL users are often restricted to `localhost` connections. To check and fix:

1. SSH into `WebAppPOC` and open MySQL:
   ```bash
   mysql -u root
   ```

2. Check the host setting for the `nodeapp` user:
   ```sql
   SELECT user, host FROM mysql.user WHERE user = 'nodeapp';
   ```

3. If `host` shows `localhost` or `127.0.0.1` instead of `%`, fix it:
   ```sql
   RENAME USER 'nodeapp'@'localhost' TO 'nodeapp'@'%';
   FLUSH PRIVILEGES;
   ```
   Or drop and recreate the user:
   ```sql
   DROP USER 'nodeapp'@'localhost';
   CREATE USER 'nodeapp'@'%' IDENTIFIED WITH mysql_native_password BY 'student12';
   GRANT ALL PRIVILEGES ON *.* TO 'nodeapp'@'%';
   FLUSH PRIVILEGES;
   ```

4. Retry the `mysqldump` command from the Learner Lab Console.

---

### Prompt
> That still doesn't work. I don't think the Learner Lab is inside the same VPC as the IP is `172.17.0.2`.

### Response
Correct — the Learner Lab Console runs in a separate environment (`172.17.x.x`) with no direct access to the private IP of your `WebAppPOC` instance.

**Solution:** Run the `mysqldump` from within the VPC using `WebAppAppServer`, which is already inside `WebAppVPC`:

1. SSH into `WebAppAppServer` via EC2 Instance Connect.
2. Install the MySQL client if needed:
   ```bash
   sudo apt install mysql-client -y
   ```
3. Run the dump, replacing `<EC2instancePrivateIP>` with the private IP of `WebAppPOC`:
   ```bash
   mysqldump -h <EC2instancePrivateIP> -u nodeapp -p --database=STUDENTS > data.sql
   # Password: student12
   ```
4. Import directly into RDS from the same machine:
   ```bash
   mysql -h <RDSEndpoint> -u nodeapp -p STUDENTS < data.sql
   # Password: wmcc26db
   ```

`WebAppAppServer` can reach both the private IP of `WebAppPOC` and the RDS endpoint, making it an effective jump host for the migration.

---

### Prompt
> Could you update the Phase 1 `.yaml` to reflect the changes we made in Phase 2?

### Response
Here's a summary of what changed from Phase 1:

**Removed:**
- The `WebAppPOC` monolith instance and its MySQL database.
- The MySQL inbound rule from `WebAppAPPSG` (the DB now has its own security group).

**Added:**
- `PrivateSubnet1` (AZ1, `10.0.2.0/24`) and `PrivateSubnet2` (AZ2, `10.0.4.0/24`) with a private route table (`WebAppPrivateRT`) that has no internet gateway route.
- `WebAppDBSG` — a dedicated security group for RDS, allowing MySQL only from within the VPC (`10.0.0.0/16`).
- `WebAppDBSubnetGroup` — required by RDS, spanning both private subnets across two AZs.
- `WebAppDB` — the RDS MySQL instance in the private subnets with no public access.
- `MyDBSecret` — a Secrets Manager secret that automatically populates the RDS endpoint using `!Sub` and `!GetAtt`.
- `WebAppAppServer` — the new decoupled web server EC2 instance with `LabInstanceProfile` attached.

> ℹ️ Note: The `DBPassword` is exposed as a parameter with a default value for convenience. For extra security, remove the default or set `NoEcho: true` (already set).

**Output:** `webapp-phase2.yaml`

---

### Prompt
> Can we move on to Phase 3? Outline the needs for Phase 3.

### Response
**Goal:** Make the application highly available and scalable by adding load balancing and auto scaling across two Availability Zones.

#### New Infrastructure Needed

**1. Public Subnet 2**
- A second public subnet in AZ2 (same AZ as Private Subnet 2)
- CIDR: `10.0.3.0/24`, auto-assign public IPv4 enabled
- Must be associated with the main public route table

**2. Application Load Balancer (ALB)**
- Name: `WebAppALB`, spanning both public subnets across both AZs
- Uses the `WebAppAPPSG` security group
- Needs a Target Group (`WebAppTG`) of type Instances pointing at `WebAppVPC`
- Record the ALB DNS name — this becomes the new URL for the app

**3. Amazon Machine Image (AMI)**
- A snapshot of the current `WebAppAppServer` instance, named `WebAppAMI`
- Used as the base image for the Auto Scaling launch template

**4. Launch Template**
- Name: `WebAppTemplate`, based on `WebAppAMI`
- Instance type: `t3.micro`, Key pair: `vockey`
- Security group: `WebAppAPPSG`, IAM profile: `LabInstanceProfile`

**5. Auto Scaling Group**
- Name: `WebAppAutoScalingGroup`, uses `WebAppTemplate`
- Spans both public subnets (both AZs)
- Attached to `WebAppTG`, health check type: ELB
- Capacity: Min 1, Desired 1, Max 4
- Scaling policy: Target tracking on Average CPU utilisation at 30%
- Instances tagged `Name: Auto Scaling Instance`

#### Testing Requirements
- Access the app via the ALB DNS name (not a direct EC2 IP).
- Run load testing using the `loadtest` Node.js tool to push CPU over 30% and trigger scale-out.
- Monitor scaling activity and CPU graphs in the AWS Console (set timescale to 15 minutes).
- Save screenshots of monitoring graphs and note the loadtest commands used.

#### Key Differences from Phase 2
- All traffic goes through the ALB — no direct EC2 IP access.
- Individual EC2 instances are now disposable and managed by the Auto Scaling group.
- AMI creation is a manual prerequisite before deploying the CloudFormation template.

---

### This response from the model was not very descriptive, especially compared to the original doc. I had to reference the doc multiple times even with the models summarization.

### Prompt
> Can we focus in on the final load testing task?

### Response

#### Setup — Installing `loadtest`
Run the following on each machine you want to use for load generation (use CS lab machines, not your personal machine):

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Initialise nvm (run every time you log in)
. ~/.nvm/nvm.sh

# Install Node.js
nvm install 25.7.0

# Install loadtest
npm install loadtest
```

#### Running the Load Test
Replace `<LoadBalancerDNS>` with your ALB DNS name from the CloudFormation outputs:

```bash
~/node_modules/loadtest/bin/loadtest.js --rps 1000 -c 1000 -n 1000000 -k http://<LoadBalancerDNS>
```

- `--rps` — requests per second
- `-c` — concurrent users
- `-n` — total number of requests
- `-k` — enables keep-alive connections

Press `Ctrl+C` to stop at any time.

#### What You're Trying to Achieve
Push average CPU utilisation above 30% to trigger the Auto Scaling group to add new instances. To help:
- Progressively increase `--rps` and `-c`.
- Run the command on multiple lab machines simultaneously.
- A single machine may not generate enough load on its own.

#### What to Monitor in the AWS Console
- **Load Balancer monitoring tab** — rising request count and latency confirms the frontend is under load.
- **EC2 Auto Scaling Group** — watch the instance count increase from 1 toward 4.
- **EC2 CPU monitoring** — should show spikes above 30%.
- Set the timescale to **15 minutes** for a clearer real-time view.

#### What to Save for Submission
- The exact `loadtest` command(s) used.
- Screenshots of monitoring graphs showing CPU load and instance scaling.
- A screen capture showing load generation success (latency, error rates, instance count changes).

#### Tips
- Ignore warnings from the `loadtest` tool — let it run.
- Check that nobody else is using the lab machine before hammering it (`finger` or `w` commands show who's logged in).
- If the ALB shows instances as **Unhealthy**, verify the health check path is `/` and port 80 is open in the security group.

---

### Prompt
> Could you update the Phase 2 YAML to work with Phase 3 modifications (ALB + Auto Scaling)?

### Response
Here's a summary of what changed from Phase 2:

**Added:**
- `PublicSubnet2` (`10.0.3.0/24`, AZ2) — required for the ALB to span two AZs.
- `WebAppTG` — the ALB target group, health checking on `GET /` over port 80.
- `WebAppALB` — internet-facing Application Load Balancer spanning both public subnets.
- `WebAppALBListener` — forwards HTTP port 80 traffic to `WebAppTG`.
- `WebAppLaunchTemplate` — replaces the single `WebAppAppServer` instance; uses `t3.micro` and the AMI you create manually.
- `WebAppAutoScalingGroup` — min 1, desired 1, max 4 instances across both public subnets, attached to the ALB target group.
- `WebAppScalingPolicy` — target tracking on average CPU at 30%.

**Removed:**
- The standalone `WebAppAppServer` EC2 instance — instances are now managed entirely by the Auto Scaling group.

> ⚠️ **Before deploying:** You must manually create `WebAppAMI` from your existing `WebAppAppServer` instance and pass its AMI ID as the `WebAppAMIId` parameter. The app URL is now the ALB DNS name, found in the stack Outputs.

**Output:** `webapp-phase3.yaml`

---

### Prompt
> Can we move on to the final phase?

### Response

#### Part 1 — Setting Up the Dev Environment

1. Install Node.js via your preferred method:
   - **Mac:** `brew install node`
   - **Linux:**
     ```bash
     curl -fsSL https://deb.nodesource.com/setup_25.x | bash -
     apt install -y nodejs
     ```
   - **Windows:** download from the Node.js archive.

2. Download and unzip the application code:
   ```bash
   wget https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACCAP1-1-91571/1-lab-capstone-project-1/code.zip
   unzip code.zip -x "resources/codebase_partner/node_modules/*"
   cd resources/codebase_partner
   ```

3. Install required dependencies:
   ```bash
   npm install aws aws-sdk uuid @aws-sdk/client-dynamodb @aws-sdk/util-dynamodb
   ```

4. Copy your AWS credentials from the Academy console into `~/.aws/credentials`:
   ```
   [default]
   aws_access_key_id = YOUR_KEY
   aws_secret_access_key = YOUR_SECRET
   aws_session_token = YOUR_TOKEN
   ```

5. In the AWS Console (`us-east-1`), go to DynamoDB and create a table:
   - Table name: your choice (e.g. `Students`)
   - Partition key: `id` (type: String)
   - Leave all other settings as default.

#### Part 2 — Rewriting `supplier.model.js`

Replace the imports at the top of the file:

```javascript
const { ListTablesCommand, DynamoDBClient, PutItemCommand,
        GetItemCommand, ScanCommand, UpdateItemCommand,
        DeleteItemCommand } = require("@aws-sdk/client-dynamodb");
const { marshall, unmarshall } = require("@aws-sdk/util-dynamodb");
const { v4: uuidv4 } = require('uuid');

// comment out the old db config
// const dbConfig = require("../config/config");

const client = new DynamoDBClient({ region: "us-east-1" });
const TABLE_NAME = "Students"; // match whatever you named your table
```

Rewrite each function using the async/await pattern:

**`getAll`:**
```javascript
Supplier.getAll = (result) => {
  (async () => {
    try {
      const data = await client.send(new ScanCommand({ TableName: TABLE_NAME }));
      const students = data.Items.map((item) => unmarshall(item));
      result(null, students);
    } catch (e) {
      result(e, null);
    }
  })();
};
```

**`create`** (uses `uuidv4` instead of auto-increment):
```javascript
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
```

**`findById`:**
```javascript
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
```

**`updateById`:**
```javascript
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
```

**`remove`:**
```javascript
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
```

You can remove the `dbConnect` function entirely — the DynamoDB client handles connections automatically.

Test locally by running:
```bash
export APP_PORT=80
npm start
```

#### Part 3 — Deploying to AWS

1. Repack your modified code:
   ```bash
   cd /path/to/home/ubuntu
   zip -r mycode.zip resources/codebase_partner -x "resources/codebase_partner/node_modules/*"
   ```

2. In S3, create a new bucket (e.g. `webapp-phase4-yourname`) and upload `mycode.zip`. Either generate a presigned URL or set the object to public read.

3. Update the Phase 3 CloudFormation YAML:
   - Add an `AWS::DynamoDB::Table` resource for the Students table.
   - Update the launch template user data to pull from your S3 bucket.
   - Add the DynamoDB table name as an environment variable in the startup script.
   - Ensure `LabInstanceProfile` has the necessary DynamoDB permissions (it should via `LabRole`).

4. Deploy the updated stack and test via the ALB DNS name.

#### Submission README — Points to Address
- **What was harder with DynamoDB?** No auto-increment IDs, no SQL joins, async exceptions, type marshalling.
- **What was easier?** No schema migrations, no connection pooling, scales automatically, no server to manage.
- **Why the tradeoff?** DynamoDB suits high-scale simple lookups; MySQL suits complex relational queries.

---

### Prompt
> Could you also update this function to work with DynamoDB?
> ```javascript
> Supplier.removeAll = result => { ... };
> ```

### Response

```javascript
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
```

DynamoDB has no bulk delete equivalent of `DELETE FROM table`, so you must scan for all records first, then delete each one by key. `Promise.all()` fires all delete requests in parallel for efficiency. Make sure `DeleteItemCommand` is included in your imports.

---

## March 4 — Phase 4 Errors

### Prompt
> Can you suggest a fix for this error?
> ```
> Error [ERR_REQUIRE_ESM]: require() of ES Module uuid/dist-node/index.js not supported.
> ```

### Response
This is a common compatibility issue — newer versions of the `uuid` package are ES Modules only and don't support `require()`. The simplest fix is to install an older version:

```bash
npm install uuid@9
```

Version 9 is the last version that supports `require()` and is fully compatible with the codebase. No code changes needed.

Alternatively, use Node's built-in `crypto` module instead:

```javascript
const { randomUUID } = require('crypto');
```

Then replace any call to `uuidv4()` with `randomUUID()`. This avoids the dependency entirely and is the recommended approach for newer Node.js projects.

---

### Prompt
> How should I modify `getAll` so it does not throw an error when no students are retrieved?

### Response

```javascript
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
```

The guard clause handles two cases:
- `data.Items` is `undefined` — DynamoDB's `ScanCommand` can omit the `Items` field entirely on an empty table, causing `.map()` to throw.
- `data.Items` is an empty array — handles the case where the field exists but has no entries.

Returning `[]` rather than `null` is better since the app likely expects an iterable and an empty array will render cleanly as "no students found" in the UI.

---

### Prompt
> Should I generate a presigned URL or set the object to public read? Also, can you update the Phase 3 YAML for the Phase 4 deployment?

### Response
**Use a presigned URL.** It keeps your S3 bucket private while still allowing EC2 instances to download the file during startup. Public read exposes your code to anyone on the internet, which is bad practice. Presigned URLs also expire automatically, which is cleaner.

To generate one in the AWS Console: go to your S3 bucket, click on `mycode.zip`, and choose **Object actions → Share with a presigned URL**. Set an expiry long enough for your deployment window (a few hours is fine).

**Summary of Phase 4 YAML changes from Phase 3:**

**Removed:**
- All RDS resources (`WebAppDB`, `WebAppDBSubnetGroup`, `WebAppDBSG`).
- Both private subnets and the private route table — DynamoDB is accessed via the internet, no private subnet required.
- Secrets Manager secret — DynamoDB uses IAM via `LabInstanceProfile`.

**Added:**
- `StudentsTable` — a DynamoDB table with `id` (String) as the partition key, using on-demand billing (`PAY_PER_REQUEST`).
- `CodeZipPresignedUrl` parameter — paste your presigned S3 URL at deploy time.
- Updated user data in the launch template to pull from S3, install the correct dependencies (`uuid@9`, DynamoDB SDK), and inject `AWS_REGION` and `DYNAMODB_TABLE` as environment variables.

> ℹ️ Make sure `TABLE_NAME` in `supplier.model.js` reads from the environment variable:
> ```javascript
> const TABLE_NAME = process.env.DYNAMODB_TABLE || "Students";
> ```

**Output:** `webapp-phase4.yaml`

---

## March 5 — DynamoDB Credentials Debugging

### Prompt
> I am getting a credentials error on my local instance of the DynamoDB-powered backend. How do I connect to the DynamoDB table on the lab AWS account?

### Response

**Step 1 — Get your credentials**
1. Open the AWS Academy console.
2. Click **AWS Details** (top right of the lab page).
3. Click **Show** next to AWS CLI credentials — you'll see three values: `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`.

**Step 2 — Add them to your local machine**

Paste them into `~/.aws/credentials`:
```
[default]
aws_access_key_id = PASTE_HERE
aws_secret_access_key = PASTE_HERE
aws_session_token = PASTE_HERE
```

Or export them as environment variables in your terminal:
```bash
export AWS_ACCESS_KEY_ID=PASTE_HERE
export AWS_SECRET_ACCESS_KEY=PASTE_HERE
export AWS_SESSION_TOKEN=PASTE_HERE
```

**Step 3 — Make sure the region is set**

In `~/.aws/config`:
```
[default]
region = us-east-1
```

Or as an environment variable: `export AWS_REGION=us-east-1`

> ⚠️ AWS Academy credentials expire every few hours when the lab session ends. If you get a credentials error in a future session, repeat Step 1 and paste fresh credentials.

---

### Prompt
> Is there anything else that needs to happen to connect specifically to the DynamoDB instance?

### Response
Yes — ensure your `DynamoDBClient` is explicitly configured with the region in `supplier.model.js`:

```javascript
const client = new DynamoDBClient({ region: "us-east-1" });
```

Also make sure the table name in your code matches exactly what you named your table in the AWS Console — DynamoDB is case-sensitive (`Students` and `students` are different tables):

```javascript
const TABLE_NAME = process.env.DYNAMODB_TABLE || "Students"; // must match exactly
```

Unlike MySQL, DynamoDB requires no connection string, no host, no port, and no database name. The SDK handles the connection automatically using your credentials, the region set in the client, and the table name passed in each command.

---

### Prompt
> I am still getting this error: `CredentialsProviderError: Could not load credentials from any providers`. I loaded all my keys as environment variables but it still isn't being properly loaded.

### Response

**1. Verify the environment variables are actually set**

In the same terminal session where you're running the app:
```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_SESSION_TOKEN
```

If any print blank, they weren't set correctly. Environment variables set in one terminal are not shared with other terminals — make sure you're running `npm start` in the same terminal where you ran the `export` commands.

**2. Try setting them explicitly in the client**

As a quick diagnostic test, hardcode them in the client initialisation:
```javascript
const client = new DynamoDBClient({
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    sessionToken: process.env.AWS_SESSION_TOKEN
  }
});
```

This forces the SDK to read from environment variables rather than its default provider chain, which can sometimes fail in certain environments.

**3. Check the credentials file as a fallback**

```bash
mkdir -p ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = PASTE_HERE
aws_secret_access_key = PASTE_HERE
aws_session_token = PASTE_HERE
EOF

cat > ~/.aws/config << EOF
[default]
region = us-east-1
EOF
```

---

### Prompt
> When I hardcode the keys, I get a separate error saying the keys are invalid even though they are directly pasted from the Learner Lab.

### Response
This is a known AWS Academy quirk — the credentials block in the console can include extra whitespace, hidden characters, or line breaks when copied, corrupting the key values visually.

**Option 1 — Use the pre-formatted credentials block**
1. In the Academy console, click **AWS Details**.
2. Click **Download PEM** or look for the **"AWS CLI: Show"** button.
3. Copy the entire block that looks like:
   ```
   [default]
   aws_access_key_id=ASIA...
   aws_secret_access_key=...
   aws_session_token=...
   ```
4. Paste it exactly as-is into `~/.aws/credentials` with no modifications.
5. Remove the hardcoded credentials from the client and revert to:
   ```javascript
   const client = new DynamoDBClient({ region: "us-east-1" });
   ```

**Option 2 — Restart the lab session**
Academy credentials can also become invalid if the lab session has timed out. Try clicking **End Lab** then **Start Lab** again, wait for the green dot next to AWS, then copy fresh credentials.

**Option 3 — Verify key format**
A valid set of Academy credentials should look like:
- `aws_access_key_id` starts with `ASIA` (temporary keys always start with `ASIA`, not `AKIA`)
- `aws_secret_access_key` is a 40-character mixed-case alphanumeric string
- `aws_session_token` is a long string, typically several hundred characters

If any of these don't match, the session has likely expired and needs restarting.

---

### Prompt
> I get the previous credentials provider error when using `~/.aws/credentials`. It doesn't recognise this as a proper path.

### Response

**1. Verify the file path and format**

The file must be at `~/.aws/credentials` with no file extension. Check it:
```bash
cat ~/.aws/credentials
```

It should look exactly like this with no spaces around the `=` signs:
```
[default]
aws_access_key_id=ASIA...
aws_secret_access_key=...
aws_session_token=...
```

**2. Check `AWS_SDK_LOAD_CONFIG`**

The v3 SDK sometimes needs to be explicitly told to look at the credentials file:
```bash
export AWS_SDK_LOAD_CONFIG=1
```

Then try running the app again in the same terminal.

**3. Check if `AWS_PROFILE` is set to something unexpected**
```bash
echo $AWS_PROFILE
```

If this prints anything other than blank or `default`, unset it:
```bash
unset AWS_PROFILE
```

**4. Explicitly point the SDK at the credentials file in code**
```javascript
const { fromIni } = require("@aws-sdk/credential-provider-ini");

const client = new DynamoDBClient({
  region: "us-east-1",
  credentials: fromIni({ profile: "default" })
});
```

Install the provider package first:
```bash
npm install @aws-sdk/credential-provider-ini
```

> **Recommended first step:** Option 2 (`AWS_SDK_LOAD_CONFIG=1`) is the most common fix for this specific issue with the v3 SDK and requires no code changes.

---

## March 5 — Phase 4 Deployment Issues

### Prompt
> Something is wrong with the new instances on AWS. They use the old code rather than the new Phase 4 code when we create the stack using the Phase 4 YAML. I think something is wrong with the images, but I don't know how to fix it.

### Response
This is a classic **AMI baking problem**. The `WebAppAMIId` you're passing to the Phase 4 stack is the AMI created from the Phase 3 `WebAppAppServer`, which has the old MySQL-based code baked into it. When Auto Scaling spins up new instances from that AMI, they start with the old code regardless of the user data script.

**Option 1 — Rebake the AMI (recommended)**
1. Launch a temporary EC2 instance using the Phase 4 user data script so it pulls `mycode.zip` from S3.
2. Verify the app is running correctly with DynamoDB.
3. Create a new AMI: **Actions → Image and templates → Create image**, named `WebAppAMI-Phase4`.
4. Wait for the AMI status to show **Available**.
5. Redeploy the Phase 4 stack passing the new AMI ID as `WebAppAMIId`.

**Option 2 — Remove the AMI dependency entirely**

Use a plain Ubuntu AMI and let the user data script handle everything at boot. Change `WebAppLaunchTemplate` in the Phase 4 YAML:

```yaml
WebAppLaunchTemplate:
  Type: AWS::EC2::LaunchTemplate
  Properties:
    LaunchTemplateName: WebAppTemplate
    LaunchTemplateData:
      ImageId: !Ref LatestUbuntuAMI  # changed from WebAppAMIId
      InstanceType: t3.micro
      ...
```

Remove the `WebAppAMIId` parameter entirely. Every new instance will bootstrap itself from your S3 zip on startup.

**Option 2 is the better long-term approach** — the stack becomes fully self-contained and redeployable with no manual AMI creation step. Instances take slightly longer to become healthy but for a class project that's not a concern.

---

### Prompt
> Why is my AWS EC2 instance getting this error when I run `rc.local`?
> ```
> SyntaxError: Unexpected token '?'
> ```

### Response

**The Problem:** Your EC2 instance is running an outdated version of Node.js that doesn't support the nullish coalescing operator (`??`). The `??` operator requires Node.js ≥ 14, but your system Node is older. The AWS SDK v3 requires Node.js 14+.

**Why `rc.local` specifically fails:** When you run the app manually you're likely using a newer Node.js installed via `nvm`. But `rc.local` runs as root at boot time using the system's default Node.js, which doesn't have `nvm` in its `PATH`.

**Fix — Install Node.js 18 LTS system-wide:**

```bash
# Check your Node versions
node --version          # your shell (nvm)
sudo node --version     # system / root
/usr/bin/node --version # system default path

# Install Node 18 system-wide
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
sudo node --version  # should now show v18.x
```

| | Cause | Fix |
|---|---|---|
| Summary | The `??` operator requires Node.js ≥ 14; your system Node is older | Install Node 18 LTS system-wide via NodeSource |
| Why only `rc.local` | `rc.local` runs as root without `nvm`, using the old system Node | — |

---

### Prompt
> How should I change the user data in the CloudFormation template to fix this?

### Response

```yaml
UserData:
  Fn::Base64: !Sub |
    #!/bin/bash -xe
    apt update -y
    apt install -y unzip wget curl

    # Install Node.js 18 LTS via NodeSource (replaces outdated apt nodejs)
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs

    # Download your modified DynamoDB-enabled code from S3
    wget "${CodeZipPresignedUrl}" -O /home/ubuntu/mycode.zip
    cd /home/ubuntu
    unzip mycode.zip -x "resources/codebase_partner/node_modules/*"
    cd resources/codebase_partner
    npm install aws aws-sdk uuid@9 @aws-sdk/client-dynamodb @aws-sdk/util-dynamodb
    export APP_PORT=80
    export AWS_REGION=us-east-1
    export DYNAMODB_TABLE=STUDENTS
    npm start &

    # Write rc.local using the full system node path
    cat > /etc/rc.local << 'EOF'
    #!/bin/bash -xe
    cd /home/ubuntu/resources/codebase_partner
    export APP_PORT=80
    export AWS_REGION=us-east-1
    export DYNAMODB_TABLE=STUDENTS
    /usr/bin/npm start
    EOF
    chmod +x /etc/rc.local
```

**Key changes:**
1. **Node.js 18 via NodeSource** — replaces `apt install nodejs` (which gives Node 12) with the NodeSource setup script that installs v18 system-wide at `/usr/bin/node`.
2. **`cat > /etc/rc.local << 'EOF'`** — replaces the `echo` heredoc with a proper `cat` heredoc. The single-quoted `'EOF'` prevents `$` variables from being interpolated by the outer bash script, so exports are written literally into `rc.local`.

---

### Prompt
> Is there any way to just modify the image to make this work instead?

### Response
Yes — create a custom AMI with Node.js 18 pre-installed, then reference it in your Launch Template instead of the Ubuntu SSM parameter.

**Step 1 — Prepare a Base Instance**

Launch a plain Ubuntu 22.04 instance, SSH in, then run:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -
sudo apt install -y nodejs unzip wget
node --version  # should show v18.x
```

**Step 2 — Create the AMI**
1. In the EC2 console, select your instance.
2. **Actions → Image and Templates → Create Image**
3. Name it `WebAppAMI-Node18` and wait for it to become **Available** (~a few minutes).
4. Copy the resulting AMI ID (e.g. `ami-0abc123...`).

**Step 3 — Update Your CloudFormation Template**

Replace the `LatestUbuntuAMI` parameter:
```yaml
Parameters:
  WebAppAMIId:
    Type: String
    Description: 'AMI ID of WebAppAMI with Node.js 18 pre-installed'
```

And in the Launch Template:
```yaml
WebAppLaunchTemplate:
  ...
  LaunchTemplateData:
    ImageId: !Ref WebAppAMIId   # swap this in
```

### I think this response from the model should not have been repetitive. The model should have seen this response already in there and might make me think this is a new idea, even though it isn't.

The user data can then skip the Node.js installation step entirely.

| Approach | Pros | Cons |
|---|---|---|
| Custom AMI | Faster boot, no NodeSource dependency at launch | AMI must be manually updated when Node needs upgrading |
| NodeSource in UserData | Always fresh install, no manual AMI management | Slower boot, external dependency at launch time |

The AMI approach is generally better for Auto Scaling groups since instances boot faster and don't depend on external package sources being available at launch.

---

### Prompt
> Ok I think I want to keep your original solution. Could you clean up your UserData solution so it works without needing to make my own image?

### Response

```yaml
UserData:
  Fn::Base64: !Sub |
    #!/bin/bash -xe
    apt update -y
    apt install -y unzip wget curl

    # Install Node.js 18 LTS via NodeSource
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs

    # Download and extract app code
    wget "${CodeZipPresignedUrl}" -O /home/ubuntu/mycode.zip
    cd /home/ubuntu
    unzip mycode.zip -x "resources/codebase_partner/node_modules/*"
    cd resources/codebase_partner
    npm install aws aws-sdk uuid@9 @aws-sdk/client-dynamodb @aws-sdk/util-dynamodb

    # Write rc.local before starting the app
    cat > /etc/rc.local << 'EOF'
    #!/bin/bash -xe
    cd /home/ubuntu/resources/codebase_partner
    export APP_PORT=80
    export AWS_REGION=us-east-1
    export DYNAMODB_TABLE=STUDENTS
    /usr/bin/npm start
    EOF
    chmod +x /etc/rc.local

    # Start the app for this first boot
    export APP_PORT=80
    export AWS_REGION=us-east-1
    export DYNAMODB_TABLE=STUDENTS
    npm start &
```

**Cleanups from the previous version:**
- `rc.local` is written before starting the app — better ordering in case anything goes wrong.
- Removed `npm` from the initial `apt install` — NodeSource's Node.js package already includes `npm`, so installing it separately could cause version conflicts.
- Consistent env vars — both the first-boot `npm start` and `rc.local` use the same three exports, making them easier to update in one place.