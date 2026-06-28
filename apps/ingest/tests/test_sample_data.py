from src.sample_data import sample_startups

def test_sample_count():
    assert len(sample_startups()) >= 4
    
def test_uniqueness():
    startups = sample_startups()
    assert len({s.normalized_name for s in startups}) == len(startups)
    
