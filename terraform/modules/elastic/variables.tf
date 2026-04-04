variable "region" {
  type = string
}

variable "deployment_name" {
  type = string
}

variable "secret_name" {
  type = string
}

variable "elastic_api_key" {
  type      = string
  sensitive = true
}
