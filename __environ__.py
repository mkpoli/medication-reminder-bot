import os

from enum import Enum
from pathlib import Path

BASE_DIR = Path(__file__).parent

if not (TOKEN := os.environ.get('TELEGRAM_BOT_TOKEN')):
    with open(BASE_DIR / 'TOKEN') as f:
        TOKEN = f.read().strip()

if not TOKEN:
    raise KeyError('No TOKEN found!')


# Change the name of environment variable to be read here
DEPLOY_ENV_VAR_NAME = 'DEPLOY_ENV'

class DeploymentEnvironment(Enum):
    PRODUCTION = 'prod'
    DEVELOPMENT = 'dev'
    STAGING = 'stage'
    
    def __str__(self) -> str:
        return str(self.value)

DEPLOYMENT_ENVIRONMENT_REPRESENTATIONS = {
    DeploymentEnvironment.DEVELOPMENT: {'dev', 'development', 'trunk'},
    DeploymentEnvironment.STAGING: {'stage','staging', 'demo'},
    DeploymentEnvironment.PRODUCTION: {'prod','production', 'live'},
}

DEPLOY_ENV_VAR_VALUE = os.environ.get('DEPLOY_ENV', default='').strip().lower()

DEPLOYMENT_ENVIRONMENT = None
for deploy_env in DeploymentEnvironment:
    if DEPLOY_ENV_VAR_VALUE in DEPLOYMENT_ENVIRONMENT_REPRESENTATIONS[deploy_env]:
        DEPLOYMENT_ENVIRONMENT = deploy_env
        break
else:
    DEPLOYMENT_ENVIRONMENT = DeploymentEnvironment.DEVELOPMENT
        
# Check if in specified mode (bools)
DEVELOPMENT_MODE = DEPLOYMENT_ENVIRONMENT is DeploymentEnvironment.DEVELOPMENT
PRODUCTION_MODE = DEPLOYMENT_ENVIRONMENT is DeploymentEnvironment.PRODUCTION
STAGING_MODE = DEPLOYMENT_ENVIRONMENT is DeploymentEnvironment.STAGING
