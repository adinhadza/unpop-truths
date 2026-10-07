# unpop-truths

Publishes finished Reels to the Unpopular Truths Facebook page.

The "Post Reel to Facebook Page" workflow takes a link to a finished MP4 and a caption,
hands the video to Facebook, and waits until the Reel is live.

## Secrets required (Settings > Secrets and variables > Actions)

- `FB_PAGE_ID`: the numeric ID of the Facebook page
- `FB_PAGE_TOKEN`: a page access token with `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
