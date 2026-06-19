const { BasePage } = require('./BasePage');

class LoginPage extends BasePage {
  constructor(page) {
    super(page);
    // react-hook-form sets the `name` attribute; use that for reliable selection.
    this.usernameInput    = page.locator('[name="username"]');
    this.passwordInput    = page.locator('[name="password"]');
    this.submitButton     = page.getByRole('button', { name: /sign in/i });
    this.registerLink     = page.getByRole('link', { name: /create one/i });
    this.forgotPwdLink    = page.getByRole('link', { name: /forgot password/i });
    this.heading          = page.getByRole('heading', { name: 'FitTrack' });
  }

  async goto() {
    await this.page.goto('/login');
    await this.heading.waitFor();
  }

  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

module.exports = { LoginPage };
