const { BasePage } = require('./BasePage');

class ProfilePage extends BasePage {
  constructor(page) {
    super(page);
    this.heading        = page.getByRole('heading', { name: 'Profile & settings', exact: true });
    this.firstNameInput = page.locator('[name="first_name"]');
    this.lastNameInput  = page.locator('[name="last_name"]');
    this.emailInput     = page.locator('[name="email"]');
    // The form has multiple submit buttons (one per card); target the Account card's
    this.saveButton     = page.getByRole('button', { name: /save changes/i }).first();
  }

  async goto() {
    await this.page.goto('/profile');
    await this.heading.waitFor();
  }

  async updateName(firstName, lastName) {
    await this.firstNameInput.fill(firstName);
    if (lastName !== undefined) await this.lastNameInput.fill(lastName);
    await this.saveButton.click();
  }
}

module.exports = { ProfilePage };
