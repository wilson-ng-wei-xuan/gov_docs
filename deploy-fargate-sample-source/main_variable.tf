variable "agency_code" {
  type = string
  default = "demo-demo-test"
}

variable "dept" {
  type  = string
  default = "demo-demo-test"
}

variable "project_code" {
  type = string
  default = "demo-demo-test"
}

variable "project_desc" {
  type = string
  default = ""
}

variable "zone" {
  type = string
  default = "ez"
}

variable "tier" {
  type = string
  default = "app"
}

variable "opsend-date" {
  type = string
  default = "dec 2099"
}


#######################################################
## project specific
#######################################################
# variable "ecr_repo" {
#     type = string
#     default = "ecr-dsaid-prodezapp-launchpad"
# }

variable "ecs_task_cpu" {
    type = string
    default = "256"
}

variable "ecs_task_memory" {
    type = string
    default = "512"
}

variable "ecs_port" {
    type = number
    default = 8501
    # default = 80 # UPDATE THIS IF NOT 80
}

# variable "lb_target_group_health_check_path" {
#     type = string
#     default = "/demo-demo-test"
#     # default = "/" # UPDATE THIS, typically same as project-code
# }

#######################################################
## environment specific
#######################################################
variable "image_tag" {
    type = string
    default = "latest" # "v1.0.0" # "dev-david-test" # "2e681d3" # "afe187a"
}

variable "lb_listener_rule_host_header" {
    type = list
    default = ["poc.launchpad.tech.gov.sg"]
}

variable "lb_listener_rule_priority" {
    type = number
    default = 9998
}

variable "capacity_provider" {
    type = string
    default = "FARGATE_SPOT"
}

variable "retention_in_days" {
    type = number
    default = 3653
}