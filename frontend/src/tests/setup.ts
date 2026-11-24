import "@testing-library/jest-dom/vitest";

// jsdom lacks these browser APIs used by charts and animations
class RO { observe() {} unobserve() {} disconnect() {} }
(globalThis as unknown as { ResizeObserver: typeof RO }).ResizeObserver = RO;
Element.prototype.scrollIntoView = function () {};
