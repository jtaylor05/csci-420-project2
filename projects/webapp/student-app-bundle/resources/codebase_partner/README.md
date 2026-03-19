# Deployment

I deployed my project for phase 4 by resetting it from the ground up. I deleted my previous stack which I had used to develop phase 1 through 3 and replaced it with my new phase 4 stack which contained all the information needed to make my new DynamoDB backend work. This was to make sure that it would work on a fresh AWS dashboard without any other modifications.

Before I initialised my new stack, there were a few steps that needed to be taken:

- Firstly, I needed to upload my new code to an S3 bucket. The zip file I added contains the relevant information and is just a zip file of the resources directory. One needs to get a signed URL for the S3 bucket to put into the CloudFormationParameters. 

- I also slightly modified the process to skip making ones own AMI, and just directly modify the base Ubunutu image to work directly. This makes it easier to deploy on an empty account.

# Comparison

I think DynamoDB is definitely better for this particular task in cloud computing compared to mySQL. DynamoDB helps provide that layer of abstraction from the backend that we seem to strive for, allowing it to be more scalable and extendable than using mySQL. That being said, mySQL has more choice over implementation and the ability for more complex task completion. Just looking at the difference in code between the original mySQL and DynamoDB as well, DynamoDB required a lot more 'work-arounds' to achieve the same functionality as mySQL with its limited set of functions. I would also say that MySQL is easier to test with and create new products, because DynamoDB requires a cloud system or a complex custom backend version.