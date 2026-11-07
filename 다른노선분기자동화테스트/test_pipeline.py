from core.world.world import World
from run import Main


def test_pipeline_without_files():
    # 파일을 열 필요 없이 바로 테스트!
    world = World()
    main = Main()
    al_main = main._create_local_mainline(100.0, 25.0, 59375)
    al_target = main._create_local_target_track(100.0, 25.0, 59375, 7.0, 28)

    # ... world 구성 후 ...
    world.run()
    assert world.components["turnout_spec"].radius > 0