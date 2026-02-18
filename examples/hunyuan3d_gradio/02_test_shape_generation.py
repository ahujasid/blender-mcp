from pathlib import Path

from gradio_client import handle_file

from api_common import DEFAULT_IMAGE, ensure_exists, make_client


def main() -> None:
    image_path = Path(DEFAULT_IMAGE)
    ensure_exists(image_path, "test image")

    client = make_client()
    result = client.predict(
        image=handle_file(str(image_path)),
        mv_image_front=None,
        mv_image_back=None,
        mv_image_left=None,
        mv_image_right=None,
        steps=10,
        guidance_scale=5,
        seed=1234,
        octree_resolution=64,
        check_box_rembg=True,
        num_chunks=2000,
        randomize_seed=False,
        api_name="/shape_generation",
    )

    file_out, html_out, mesh_stats, seed_out = result
    print("/shape_generation ok")
    print("file_out:", file_out)
    print("mesh_stats:", mesh_stats)
    print("seed_out:", seed_out)
    print("html_out preview:", str(html_out)[:200])

if __name__ == "__main__":
    main()

# /shape_generation ok
# file_out: {'value': '/tmp/gradio/2810b6b38564e010660bbcbfbe4e51f25668051eba481abf5df41634c0d78f8e/white_mesh.glb', '__type__': 'update'}
# mesh_stats: {'model': {'shapegen': '/root/Hunyuan3D-2.1/ckpt/Hunyuan3D-2.1/hunyuan3d-dit-v2-1', 'texgen': '/root/Hunyuan3D-2.1/ckpt/models--tencent--Hunyuan3D-2.1/snapshots/da98cc870b9eefb06dd1d9f09d28c27ee7c2fd29'}, 'params': {'caption': None, 'steps': 10, 'guidance_scale': 5, 'seed': 1234, 'octree_resolution': 64, 'check_box_rembg': True, 'num_chunks': 2000}, 'number_of_faces': 20342, 'number_of_vertices': 10231, 'time': {'remove background': 0.18787145614624023, 'shape generation': 33.410457611083984, 'export to trimesh': 0.006632804870605469, 'total': 34.94183015823364}}
# seed_out: 1234
# html_out preview: 
#         <div style='height: 650; width: 100%;'>
#         <iframe src="/static/5c026f27-5d21-4766-88cf-1812cacd77fd/white_mesh.html" height="650" width="100%" frameborder="0"></iframe>
#         </div>