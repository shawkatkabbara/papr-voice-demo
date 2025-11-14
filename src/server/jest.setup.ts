/**
 * Jest setup file for configuring test environment
 *
 * This sets up a simple global fetch mock
 */

import { beforeEach, afterEach, jest } from '@jest/globals';

// Reset fetch before and after all tests
beforeEach(() => {
  global.fetch = jest.fn() as any;
});

afterEach(() => {
  jest.restoreAllMocks();
});
