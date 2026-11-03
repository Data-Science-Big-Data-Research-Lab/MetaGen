"""A thread's own generators: what it draws inside depends on its seed alone."""
import threading

from metagen.framework.rng import get_numpy_rng, get_rng, own_generators, set_seed


def test_a_thread_with_its_own_generators_draws_the_same_whatever_others_draw():
    def draws():
        return [get_rng().random() for _ in range(5)], get_numpy_rng().random(5).tolist()

    with own_generators(7):
        alone = draws()

    results = {}

    def worker(name):
        with own_generators(7):
            first = get_rng().random(), get_numpy_rng().random()
            barrier.wait()
            results[name] = first

    barrier = threading.Barrier(2)
    threads = [threading.Thread(target=worker, args=(name,)) for name in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results[0] == results[1] == (alone[0][0], alone[1][0])


def test_the_generators_of_the_process_do_not_notice():
    set_seed(3)
    expected = get_rng().random(), get_numpy_rng().random()
    set_seed(3)
    with own_generators(7):
        get_rng().random()
        get_numpy_rng().random()
    assert (get_rng().random(), get_numpy_rng().random()) == expected


def test_own_generators_end_with_the_block_also_when_it_fails():
    set_seed(3)
    process_generator = get_rng()
    try:
        with own_generators(7):
            assert get_rng() is not process_generator
            raise ValueError
    except ValueError:
        pass
    assert get_rng() is process_generator
