from pathlib import Path

from gradio_client import handle_file

from api_common import DEFAULT_GLB, ensure_exists, make_client


def main() -> None:
    glb_path = Path(DEFAULT_GLB)
    ensure_exists(glb_path, "test glb")

    # file_type in ['glb', 'obj', 'ply', 'stl']
    client = make_client()
    result = client.predict(
        file_out=handle_file(str(glb_path)),
        file_out2=handle_file(str(glb_path)),
        file_type="glb",
        reduce_face=True,
        export_texture=False,
        target_face_num=5000,
        api_name="/on_export_click",
    )
    
    html_out, download_file = result
    print("/on_export_click ok")
    print("download_file:", download_file)
    print("html_out preview:", str(html_out)[:200])


if __name__ == "__main__":
    main()

# /on_export_click ok
# download_file: {'interactive': True, 'value': '/tmp/gradio/45dde2c6b3adceb44dd8689d9f6fa917fa191fbc8c62105c82012b945eb49c98/white_mesh.glb', '__type__': 'update'}
# html_out preview: 
#         <div style='height: 650; width: 100%;'>
#         <iframe src="/static/da0024dc-4193-4bd6-a9fe-5864fc65a229/white_mesh.html" height="650" width="100%" frameborder="0"></iframe>
#         </div>