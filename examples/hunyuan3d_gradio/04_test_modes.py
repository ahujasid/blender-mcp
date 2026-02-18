from api_common import make_client


def main() -> None:
    # Create a client for the remote Gradio app.
    client = make_client()

    # Test generation mode switch endpoint.
    # ['Turbo', 'Fast', 'Standard']
    # "Turbo" usually maps to fewer inference steps for faster testing.
    gen_mode_result = client.predict(value="Turbo", api_name="/on_gen_mode_change")
    print("/on_gen_mode_change ->", gen_mode_result)

    # Test decode mode switch endpoint.
    # ['Low', 'Standard', 'High']
    # "Low" usually maps to lower octree resolution and lower memory usage.
    decode_mode_result = client.predict(value="High", api_name="/on_decode_mode_change")
    print("/on_decode_mode_change ->", decode_mode_result)


if __name__ == "__main__":
    main()

# /on_gen_mode_change -> {'value': 5, '__type__': 'update'}
# /on_decode_mode_change -> {'value': 196, '__type__': 'update'}