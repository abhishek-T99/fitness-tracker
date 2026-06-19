/**
 * Lightweight stub for lucide-react icons.
 *
 * Replaces every named export with a function component that renders a <svg>
 * carrying a data-testid so tests can assert icon presence without the full
 * lucide bundle.
 */
const React = require("react");

module.exports = new Proxy(
  {},
  {
    get(_, displayName) {
      const MockIcon = ({ className, size, strokeWidth, ...rest }) =>
        React.createElement("svg", {
          "data-testid": `icon-${String(displayName).toLowerCase()}`,
          className,
          ...rest,
        });
      MockIcon.displayName = String(displayName);
      return MockIcon;
    },
  }
);
