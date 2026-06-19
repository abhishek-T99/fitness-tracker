/**
 * Generates unique, timestamped test data strings so parallel test runs
 * never collide on human-readable names.
 */

function uid() {
  return Date.now().toString(36).slice(-5);
}

const data = {
  uid,
  workoutName:  () => `PW Workout ${uid()}`,
  goalTitle:    () => `PW Goal ${uid()}`,
  registerUser: () => ({
    first_name:       'Test',
    last_name:        'User',
    username:         `pwuser_${uid()}`,
    email:            `pwuser_${uid()}@fittrack.test`,
    password:         'TestPass123!',
    password_confirm: 'TestPass123!',
  }),
  today: () => new Date().toISOString().slice(0, 10),
};

module.exports = data;
