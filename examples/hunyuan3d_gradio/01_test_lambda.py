from api_common import make_client


def main() -> None:
    client = make_client()
    result = client.predict(api_name="/lambda")
    print("/lambda result:")
    print(result)
    
    result = client.predict(api_name="/lambda_2")
    print("/lambda_2 result:")
    print(result)

    result = client.predict(api_name="/lambda_3")
    print("/lambda_3 result:")
    print(result)
    
    result = client.predict(api_name="/lambda_4")
    print("/lambda_4 result:")
    print(result)
    
if __name__ == "__main__":
    main()

# /lambda result:
# ()
# /lambda_2 result:
# ()
# /lambda_3 result:
# ({'visible': True, 'value': True, '__type__': 'update'}, {'interactive': False, '__type__': 'update'}, {'interactive': False, '__type__': 'update'})
# /lambda_4 result:
# ()