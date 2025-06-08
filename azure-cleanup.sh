#!/bin/bash
# Azure Cleanup Script for Telogical Chatbot
# This script removes all Azure resources created for the Telogical Chatbot
#
# ⚠️ WARNING: This will delete ALL resources and data permanently!
# Use this script only when you want to completely remove the deployment
#
# Usage: ./azure-cleanup.sh

set -e  # Exit on any error

# Configuration
RESOURCE_GROUP="telogical-rg"

echo "⚠️ WARNING: This will permanently delete all Telogical Chatbot resources in Azure!"
echo "Resource Group: $RESOURCE_GROUP"
echo ""
read -p "Are you sure you want to continue? (type 'DELETE' to confirm): " confirmation

if [ "$confirmation" != "DELETE" ]; then
    echo "❌ Cleanup cancelled."
    exit 0
fi

echo "🗑️ Starting cleanup process..."

# Check if resource group exists
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "📋 Found resource group: $RESOURCE_GROUP"
    
    # List all resources before deletion
    echo "📊 Resources to be deleted:"
    az resource list --resource-group $RESOURCE_GROUP --output table
    
    echo ""
    read -p "Proceed with deletion? (y/N): " proceed
    
    if [ "$proceed" = "y" ] || [ "$proceed" = "Y" ]; then
        echo "🗑️ Deleting resource group and all resources..."
        az group delete --name $RESOURCE_GROUP --yes --no-wait
        
        echo "✅ Cleanup initiated successfully!"
        echo "📋 The resource group '$RESOURCE_GROUP' and all its resources are being deleted."
        echo "🕐 This process may take a few minutes to complete."
        echo ""
        echo "🔍 To check deletion status:"
        echo "   az group show --name $RESOURCE_GROUP"
        echo ""
        echo "✅ You can also monitor progress in the Azure Portal:"
        echo "   https://portal.azure.com/#@/resource/subscriptions/SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
    else
        echo "❌ Cleanup cancelled."
    fi
else
    echo "ℹ️ Resource group '$RESOURCE_GROUP' not found. Nothing to clean up."
fi