#/bin/bash

# Check if input data directory exists
if [ ! -d "/workspace/data/input" ]; then

    # Create input data directory
    mkdir /workspace/data/input

    # Download the data, shared as public links from Google Cloud Storage Bucket
    echo "Downloading input data..."
    wget -O /workspaces/data/input/Appendix_A_JOTR_Vegetation_Descriptions_2012.pdf https://storage.googleapis.com/ecotech_dev_demo/Appendix_A_JOTR_Vegetation_Descriptions_2012.pdf
    wget -O /workspace/data/input/table_mapping.json https://storage.googleapis.com/ecotech_dev_demo/table_mapping.json

fi

