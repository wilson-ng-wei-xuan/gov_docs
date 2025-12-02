resource "aws_cur_report_definition" "cur_report_definition" {
  report_name                = "monthly"
  time_unit                  = "MONTHLY"
  format                     = "textORcsv"
  compression                = "GZIP"
  additional_schema_elements = ["RESOURCES"]
  s3_bucket                  = data.aws_s3_bucket.cost-usage-reports.id
  s3_prefix                  = "reports"
  s3_region                  = data.aws_region.current.name
  report_versioning          = "OVERWRITE_REPORT"
  # additional_artifacts       = ["REDSHIFT", "QUICKSIGHT"]
}