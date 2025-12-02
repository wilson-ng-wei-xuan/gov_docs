resource "aws_lambda_layer_version" "lambda_layer" {

  # for_each = toset( var.lambda_layer )
  for_each  = { for entry in var.lambda_layers: "${entry.layer_name}" => entry }

  layer_name = "${local.layer_name}${each.value.layer_name}"

  filename            = "${path.root}/source/lambda_layers/${each.value.filename}"
  source_code_hash    = filebase64sha256("${path.root}/source/lambda_layers/${each.value.filename}")

  skip_destroy        = true

  compatible_runtimes = each.value.compatible_runtimes
  compatible_architectures = ["x86_64"]
  description         = "Please self test. Some layers are version agnostic while others are sensitive."
}
