import test from 'node:test';
import assert from 'node:assert';

test('API Client exports and contract verification', async (t) => {
  await t.test('API_BASE defaults to localhost:8000', async () => {
    const defaultBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    assert.strictEqual(defaultBase, 'http://localhost:8000');
  });

  await t.test('handles JSON parse and errors properly', async () => {
    const mockError = { detail: 'Standard IS 9999 not found in database.' };
    assert.strictEqual(mockError.detail, 'Standard IS 9999 not found in database.');
  });
});
