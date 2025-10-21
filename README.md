### Remove AWS Default VPCs

This Python script attempts to delete the AWS default VPC in each region.

**Requirements:**

* Tested with:
   * Python version: 3.13+
   * Boto3 version: 1.40.55
   * Botocore version: 1.40.55
* Valid AWS API keys/profile

**Usage:**

```
python -m venv venv
source venv/bin/acttivate
pip3 install -r requirements.txt
python remove_vpc.py --profile <YOUR_PROFILE> --dry-run
```

**Output:**

```
[INFO] Processing default VPC vpc-045dcf7b88fb99834 in ap-south-1 (dry-run=True)
[INFO] Detaching and deleting IGW igw-0a775ec844ec3415b from vpc-045dcf7b88fb99834
[SUCCESS] Dry-run successful (no changes made)
[SUCCESS] Dry-run successful (no changes made)
[INFO] Deleting subnet subnet-0fa0d46c02cff2fc3
[SUCCESS] Dry-run successful (no changes made)
[INFO] Deleting subnet subnet-051936b98efe38c8e
[SUCCESS] Dry-run successful (no changes made)
[INFO] Deleting subnet subnet-053f6e337da300b8a
[SUCCESS] Dry-run successful (no changes made)
[INFO] Deleting VPC vpc-045dcf7b88fb99834 in region ap-south-1
[SUCCESS] Dry-run successful (no changes made)
...
```

**References:**

* https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html

