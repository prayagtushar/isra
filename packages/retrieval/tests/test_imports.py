def test_public_retrieve_api_is_exposed():
    import isra_retrieval

    assert callable(isra_retrieval.retrieve)


def test_retrieve_function_is_importable():
    from isra_retrieval.pipeline import retrieve

    assert callable(retrieve)
