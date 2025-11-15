#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3979
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    API_BASE_URL = "http://localhost:8080/api" 
    CLU_ENDPOINT = os.environ.get("CluEndpoint", "https://botlinguarai.cognitiveservices.azure.com/")
    CLU_API_KEY = os.environ.get("CluApiKey", "BWOm0BTDjA2YdzxmyT127oAOiUAFrOZd7PQ9GgtUBkYe2ZD2yVTTJQQJ99BKACBsN54XJ3w3AAAaACOGMXaK")
    CLU_PROJECT_NAME = os.environ.get("CluProjectName", "BotVooEHotel")
    CLU_DEPLOYMENT_NAME = os.environ.get("CluDeploymentName", "DeployVooHotel")
    # Adicione suas chaves da Amadeus aqui, se já não estiverem
    AMADEUS_API_KEY = os.environ.get("AmadeusApiKey", "IaAr9IU6QvVAtZqZTqoTNRAssWMpXbWD")
    AMADEUS_API_SECRET = os.environ.get("AmadeusApiSecret", "iZTBEwwYlWjHivPG")
