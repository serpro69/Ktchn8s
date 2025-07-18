module "cloudflare" {
  source                = "./modules/cloudflare"
  cloudflare_account_id = var.cloudflare.account_id
}

module "ntfy" {
  source = "./modules/ntfy"
  auth   = var.ntfy
}

module "extra_secrets" {
  source = "./modules/extra-secrets"
  data   = var.extra_secrets
}
