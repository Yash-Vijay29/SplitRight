import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ExpensesPage from './ExpensesPage'
import { apiRequest, endpoints } from '../lib/api'

vi.mock('../context/useAuth', () => ({
  useAuth: () => ({
    accessToken: 'test-token',
    selectedGroupId: '1',
  }),
}))

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual('../lib/api')
  return {
    ...actual,
    apiRequest: vi.fn(),
  }
})

vi.mock('../components/SearchSelect', () => ({
  default: function SearchSelectMock() {
    return <div data-testid="search-select-mock" />
  },
}))

describe('ExpensesPage bill analysis flow', () => {
  beforeEach(() => {
    apiRequest.mockReset()
  })

  it('analyzes a bill and applies parsed suggestion to the expense form', async () => {
    const membersPayload = {
      results: [
        { user: { user_id: 11, name: 'Alice', email: 'alice@example.com' } },
        { user: { user_id: 22, name: 'Bob', email: 'bob@example.com' } },
        { user: { user_id: 33, name: 'Carol', email: 'carol@example.com' } },
      ],
    }

    const expensesPayload = { results: [] }

    const parsePayload = {
      extracted_charges: [
        { name: 'Pasta', quantity: 2, unit_price: '10.00', line_total: '20.00' },
      ],
      totals: {
        subtotal: '20.00',
        tax: '2.00',
        tip: '3.00',
        discounts: '0.00',
        total: '25.00',
        currency: 'USD',
      },
      suggested_expense: {
        amount: '25.00',
        expense_date: '2026-04-15',
        description: 'Cafe Rio',
      },
      confidence: 0.91,
      party_size: 3,
      warnings: [],
    }

    apiRequest.mockImplementation((path, options = {}) => {
      if (path === endpoints.groupMembers('1') && options.method !== 'POST') {
        return Promise.resolve(membersPayload)
      }

      if (path === endpoints.groupExpenses('1') && options.method !== 'POST') {
        return Promise.resolve(expensesPayload)
      }

      if (path === endpoints.groupExpenseParseBill('1') && options.method === 'POST') {
        return Promise.resolve(parsePayload)
      }

      return Promise.reject(new Error(`Unexpected API call in test: ${path}`))
    })

    const user = userEvent.setup()
    render(<ExpensesPage />)

    await waitFor(() => {
      expect(apiRequest).toHaveBeenCalledWith(endpoints.groupMembers('1'), { token: 'test-token' })
      expect(apiRequest).toHaveBeenCalledWith(endpoints.groupExpenses('1'), { token: 'test-token' })
    })

    const fileInput = screen.getByLabelText('Bill Image')
    const file = new File(['fake-image-data'], 'bill.png', { type: 'image/png' })
    fireEvent.change(fileInput, { target: { files: [file] } })

    const analyzeButton = screen.getByRole('button', { name: 'Analyze Bill' })
    const analyzeForm = analyzeButton.closest('form')
    expect(analyzeForm).not.toBeNull()
    fireEvent.submit(analyzeForm)

    await waitFor(() => {
      const parseCalled = apiRequest.mock.calls.some(
        ([path, options]) =>
          path === endpoints.groupExpenseParseBill('1') && options?.method === 'POST',
      )
      expect(parseCalled).toBe(true)
    })

    expect(await screen.findByLabelText('Parsed Total')).toHaveValue('25.00')
    expect(screen.getByText('Parser confidence: 91%')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Apply Parsed Suggestion To Expense Form' }))

    expect(screen.getByLabelText('Amount')).toHaveValue(25)
    expect(screen.getByLabelText('Date')).toHaveValue('2026-04-15')
    expect(screen.getByLabelText('Description')).toHaveValue('Cafe Rio')
    expect(
      screen.getByText(/Auto-selected 3 split member\(s\) from detected party size/i),
    ).toBeInTheDocument()
  })
})
