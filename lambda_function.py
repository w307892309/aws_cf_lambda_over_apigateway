import json
import boto3
import pandas
import os

def lambda_handler(event, context):

    access_key = os.environ.get('a_key')
    secret_key = os.environ.get('s_key')

    client_price = boto3.client('pricing', region_name='us-east-1', aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    response = client_price.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'EU (Frankfurt)'},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
        ]
    )

    label = [
        'Name',
        'API Name',
        'vCPUs',
        'Memory',
        'Instance Storage',
        'Network Perfomance',
        'Linux On Demand hourly cost',
        'Linux On Demand monthly cost',
    ]

    products = []

    for price_item in response['PriceList']:
        price_json = json.loads(price_item)
        product = []
        api_name = price_json['product']['attributes']['instanceType']

        name1 = api_name.split('.')[0]
        if name1.startswith('cc'):
            name = 'Cluster Compute'
        elif name1.startswith('cr'):
            name = 'High Memory Cluster'
        else:
            name = name1.upper()
        
        if (name1[0] == 'c' and len(name1) == 2) or name1 == 'c5d':
            name += " High-CPU"
        elif name1 == 'i3':
            name += " High I/O"
        elif name1 == 'm1':
            name += " General Purpose"
        elif name1 == 'm2' or name1 == 'r3' or name1 == 'r4':
            name += ' High-Memory'
        elif name1[0] == 'm' and len(name1) == 2:
            name += " General Purpose"
        elif name1 == 'p2':
            name += " General Purpose GPU"
        elif name1 == 'x1':
            name += ' Extra High-Memory'

        name2 = api_name.split('.')[1]
        if name2 == 'xlarge':
            name += ' Extra Large'
        elif name2 == '2xlarge':
            name += ' Double Extra Large'
        elif name2 == '4xlarge':
            name += ' Quadruple Extra Large'
        elif name2 == '8xlarge':
            name += ' Eight Extra Large'
        else:
            name += ' ' + name2.capitalize()

        product.append(name)
        product.append(price_json['product']['attributes']['instanceType'])
        product.append(price_json['product']['attributes']['vcpu'])
        product.append(price_json['product']['attributes']['memory'])
        product.append(price_json['product']['attributes']['storage'])
        product.append(price_json['product']['attributes']['networkPerformance'])
        for item in price_json['terms']['OnDemand']:
            for item2 in price_json['terms']['OnDemand'][item]['priceDimensions']:
                price = float(price_json['terms']['OnDemand'][item]['priceDimensions'][item2]['pricePerUnit']['USD'])
                product.append("$" + "%.4f" % price + " per hour")
                price = price*30
                product.append("~ $" + "%.4f" % price + " per month")
                break
            break
        products.append(product)

    df = pandas.DataFrame(data = products, columns = label)

    return df.to_markdown(index = False, tablefmt = "grid")
