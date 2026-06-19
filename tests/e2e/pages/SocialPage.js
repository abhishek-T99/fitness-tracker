const { BasePage } = require('./BasePage');

class SocialPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading   = page.getByRole('heading', { name: 'Social', exact: true });
    this.feedTab   = page.getByRole('button', { name: 'Feed' });
    this.friendsTab = page.getByRole('button', { name: 'Friends' });
    this.findTab   = page.getByRole('button', { name: 'Find people' });
  }

  async goto() {
    await this.page.goto('/social');
    await this.heading.waitFor();
  }

  async switchTab(tab) {
    const btn = { feed: this.feedTab, friends: this.friendsTab, find: this.findTab }[tab];
    await btn.click();
  }

  /** Create a post. Returns after the "Posted" toast appears. */
  async createPost(body) {
    const textarea = this.page.locator('textarea').first();
    await textarea.fill(body);
    await this.page.getByRole('button', { name: /^post$/i }).click();
    await this.page.getByText('Posted').waitFor({ timeout: 8_000 });
  }

  /** Like the first post in the feed. */
  async likeFirstPost() {
    await this.page.getByRole('button', { name: /like|heart/i }).first().click();
  }

  /** Search for users in the "Find people" tab. */
  async searchUsers(query) {
    await this.switchTab('find');
    const searchInput = this.page.getByPlaceholder(/search/i).first();
    await searchInput.fill(query);
  }
}

module.exports = { SocialPage };
