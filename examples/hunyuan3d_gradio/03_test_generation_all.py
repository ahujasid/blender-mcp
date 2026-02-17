from pathlib import Path

from gradio_client import handle_file

from api_common import DEFAULT_IMAGE, ensure_exists, make_client


def main() -> None:
    image_path = Path(DEFAULT_IMAGE)
    ensure_exists(image_path, "test image")

    # check_box_rembg: remove background
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
        api_name="/generation_all",
    )

    file_out_1, file_out_2, html_out, mesh_stats, seed_out = result
    print("/generation_all ok")
    print("file_out_1:", file_out_1)
    print("file_out_2:", file_out_2)
    print("mesh_stats:", mesh_stats)
    print("seed_out:", seed_out)
    print("html_out preview:", str(html_out)[:200])


if __name__ == "__main__":
    main()

# /generation_all ok
# file_out_1: {'value': '/tmp/gradio/c5c6acead36d71f26cfcffeff8f680f657b699bf5c20c0a9e801d83ba22c7fb7/white_mesh.obj', '__type__': 'update'}
# file_out_2: {'value': '/tmp/gradio/157496ddb966a3e7e194f9a9925f2d80d2cbee6ac8b2c7409010208fea9caced/textured_mesh.glb', '__type__': 'update'}
# mesh_stats: {'model': {'shapegen': '/root/Hunyuan3D-2.1/ckpt/Hunyuan3D-2.1/hunyuan3d-dit-v2-1', 'texgen': '/root/Hunyuan3D-2.1/ckpt/models--tencent--Hunyuan3D-2.1/snapshots/da98cc870b9eefb06dd1d9f09d28c27ee7c2fd29'}, 'params': {'caption': None, 'steps': 10, 'guidance_scale': 5, 'seed': 1234, 'octree_resolution': 64, 'check_box_rembg': True, 'num_chunks': 2000}, 'number_of_faces': 20342, 'number_of_vertices': 10231, 'time': {'remove background': 0.16553306579589844, 'shape generation': 7.269755840301514, 'export to trimesh': 0.005087375640869141, 'face reduction': 0.04608798027038574, 'texture generation': 56.29603362083435, 'convert textured OBJ to GLB': 1.3069977760314941, 'total': 66.4147641658783}}
# seed_out: 1234
# html_out preview: 
#         <div style='height: 650; width: 100%;'>
#         <iframe src="/static/a8933c09-4371-4445-a6c5-4a0c38ebe70b/textured_mesh.html" height="650" width="100%" frameborder="0"></iframe>
#         </div