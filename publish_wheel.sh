#!/bin/sh

host="$1"
job_name="$2"
s3_bucket="$3"
current_dir="$(pwd)"

for file in $current_dir/dist/*.whl
do
  aws s3 cp $file s3://$3/__new/
done

curl -XPOST http://$host/job/$job_name/build
