resource "aws_glue_catalog_database" "honey_data" {
  name = "honey_data"
}

resource "aws_glue_catalog_table" "honey_data_incoming_rotations" {
  name          = "incoming_rotations"
  database_name = "honey_data"

  parameters = {
    "classification" = "csv"
  }

  table_type = "EXTERNAL_TABLE"

  partition_keys {
    name = "year"
    type = "smallint"
  }
  partition_keys {
    name = "month"
    type = "tinyint"
  }
  partition_keys {
    name = "day"
    type = "tinyint"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.honey_data.id}/${local.incoming_rotations_path}/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      parameters = {
        "separatorChar" = ","
      }
      name                  = "OpenCSVSerde"
      serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde"
    }

    # Tired of trying to appease Athena TIMESTAMP format
    # https://aws.amazon.com/premiumsupport/knowledge-center/query-table-athena-timestamp-empty/
    columns {
      name = "datetime"
      type = "string"
    }

    columns {
      name = "rotations"
      type = "smallint"
    }
  }
}
