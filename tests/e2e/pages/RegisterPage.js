const { BasePage } = require('./BasePage');

class RegisterPage extends BasePage {
  constructor(page) {
    super(page);
    this.firstNameInput        = page.locator('[name="first_name"]');
    this.lastNameInput         = page.locator('[name="last_name"]');
    this.usernameInput         = page.locator('[name="username"]');
    this.emailInput            = page.locator('[name="email"]');
    this.passwordInput         = page.locator('[name="password"]');
    this.confirmPasswordInput  = page.locator('[name="password_confirm"]');
    this.submitButton          = page.getByRole('button', { name: /create account/i });
    this.loginLink             = page.getByRole('link', { name: /sign in/i });
    this.heading               = page.getByRole('heading', { name: /create your account/i });
  }

  async goto() {
    await this.page.goto('/register');
    await this.heading.waitFor();
  }

  async register({ first_name, last_name, username, email, password, password_confirm }) {
    if (first_name)       await this.firstNameInput.fill(first_name);
    if (last_name)        await this.lastNameInput.fill(last_name);
    await this.usernameInput.fill(username);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.confirmPasswordInput.fill(password_confirm ?? password);
    await this.submitButton.click();
  }
}

module.exports = { RegisterPage };
