import os
from unittest.mock import patch

from services.social_publisher import publish_instagram, publish_threads


@patch("services.social_publisher._post")
def test_instagram_carousel(mock_post):
    mock_post.side_effect = [{"id": "c1"}, {"id": "c2"}, {"id": "parent"}, {"id": "post"}]
    with patch.dict(os.environ, {"INSTAGRAM_USER_ID": "u", "INSTAGRAM_ACCESS_TOKEN": "t"}):
        result = publish_instagram(["https://x/1.png", "https://x/2.png"], "hello")
    assert result.post_id == "post"
    assert mock_post.call_args_list[2].args[1]["children"] == "c1,c2"


@patch("services.social_publisher._post")
def test_threads_carousel(mock_post):
    mock_post.side_effect = [{"id": "c1"}, {"id": "c2"}, {"id": "parent"}, {"id": "post"}]
    with patch.dict(os.environ, {"THREADS_ACCESS_TOKEN": "t"}):
        result = publish_threads(["https://x/1.png", "https://x/2.png"], "hello")
    assert result.post_id == "post"
    assert mock_post.call_args_list[2].args[1]["children"] == "c1,c2"
