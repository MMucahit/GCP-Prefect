from prefect.infrastructure.container import DockerContainer

## Alternative to creating DockerContainer block in UI
docker_block = DockerContainer(
    image = 'mmucahitnas/prefect:zoom', ## Insert your image here
    image_pull_policy = 'ALWAYS',
    auto_remove = True
)

docker_block.save('zoom', overwrite=True)