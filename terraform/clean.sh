#!bin/bash

aws s3 rm s3://s3-to-pg-bucket-dev --recursive
terraform destroy