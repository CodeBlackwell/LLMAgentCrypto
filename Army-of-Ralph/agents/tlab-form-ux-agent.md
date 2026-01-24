# tlab-form-ux Agent

## Mission
Improve the NewBacktest form with tooltips, client-side validation, estimated duration display, and date picker presets.

## Wave
3 (Frontend - Parallel)

## Dependencies
- Wave 2 must be complete

## Owned Paths (Exclusive Write)
- `trading_lab/web/src/pages/NewBacktest.jsx`

## Shared Paths (Read Only)
- `trading_lab/api/schemas.py`

## User Stories

### US-017: Add tooltips to form fields
**Description:** As a user, I want to understand what each backtest parameter means.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, add tooltip icons next to form labels
- [ ] Tooltips for:
  - Threshold: "Minimum confidence score (0-1) required to execute a trade"
  - Position Size: "Fraction of available cash to use per trade (0.25 = 25%)"
  - Initial Cash: "Starting capital for the backtest simulation"
- [ ] Tooltip appears on hover with dark background
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-018: Add client-side form validation
**Description:** As a user, I want immediate feedback when I enter invalid values before submitting.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, add `validationErrors` state
- [ ] Validate on blur and on submit:
  - Strategy is selected
  - End date > Start date
  - Date range <= 2 years
  - Initial cash >= $100
  - Threshold between 0 and 1
  - Position size between 0 and 1
- [ ] Show inline error messages below invalid fields (red text)
- [ ] Disable submit button when any validation fails
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-019: Add estimated duration display
**Description:** As a user, I want to know approximately how long my backtest will take before I start it.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, add duration estimate section
- [ ] Calculate based on date range (~2 seconds per trading day)
- [ ] Display: "Estimated duration: Xm Ys (N trading days)"
- [ ] Updates dynamically as dates change
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Add date picker presets
**Description:** As a user, I want quick preset buttons for common date ranges.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, change date inputs to `type="date"`
- [ ] Add preset buttons: "Last 3 months", "Last 6 months", "YTD", "Last year"
- [ ] Clicking preset populates both start and end date fields
- [ ] Typecheck passes
- [ ] Verify changes work in browser

## Implementation Notes

### Tooltip Component
```jsx
function Tooltip({ text, children }) {
  return (
    <div className="relative group inline-block">
      {children}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        {text}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
      </div>
    </div>
  );
}

// Usage
<label className="flex items-center gap-2">
  Threshold
  <Tooltip text="Minimum confidence score (0-1) required to execute a trade">
    <svg className="w-4 h-4 text-gray-400 cursor-help" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
    </svg>
  </Tooltip>
</label>
```

### Validation State
```jsx
const [validationErrors, setValidationErrors] = useState({});

const validateField = (name, value) => {
  const errors = { ...validationErrors };

  switch (name) {
    case 'strategy':
      if (!value) errors.strategy = 'Please select a strategy';
      else delete errors.strategy;
      break;
    case 'threshold':
      if (value < 0 || value > 1) errors.threshold = 'Must be between 0 and 1';
      else delete errors.threshold;
      break;
    case 'position_size':
      if (value < 0 || value > 1) errors.position_size = 'Must be between 0 and 1';
      else delete errors.position_size;
      break;
    case 'initial_cash':
      if (value < 100) errors.initial_cash = 'Must be at least $100';
      else delete errors.initial_cash;
      break;
  }

  // Date range validation
  if (formData.start_date && formData.end_date) {
    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);
    const daysDiff = (end - start) / (1000 * 60 * 60 * 24);

    if (end <= start) {
      errors.end_date = 'End date must be after start date';
    } else if (daysDiff > 730) {
      errors.end_date = 'Date range cannot exceed 2 years';
    } else {
      delete errors.end_date;
    }
  }

  setValidationErrors(errors);
  return Object.keys(errors).length === 0;
};

const hasErrors = Object.keys(validationErrors).length > 0;
```

### Duration Estimate
```jsx
const estimatedDuration = useMemo(() => {
  if (!formData.start_date || !formData.end_date) return null;

  const start = new Date(formData.start_date);
  const end = new Date(formData.end_date);
  const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

  // Approximate trading days (exclude weekends roughly)
  const tradingDays = Math.ceil(daysDiff * 5 / 7);
  const seconds = tradingDays * 2; // ~2 seconds per day

  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;

  return { tradingDays, formatted: `${mins}m ${secs}s` };
}, [formData.start_date, formData.end_date]);
```

### Date Presets
```jsx
const datePresets = [
  { label: 'Last 3 months', months: 3 },
  { label: 'Last 6 months', months: 6 },
  { label: 'YTD', ytd: true },
  { label: 'Last year', months: 12 },
];

const applyPreset = (preset) => {
  const end = new Date();
  let start;

  if (preset.ytd) {
    start = new Date(end.getFullYear(), 0, 1);
  } else {
    start = new Date();
    start.setMonth(start.getMonth() - preset.months);
  }

  setFormData({
    ...formData,
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0],
  });
};

// UI
<div className="flex gap-2 mb-4">
  {datePresets.map((preset) => (
    <button
      key={preset.label}
      type="button"
      onClick={() => applyPreset(preset)}
      className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full"
    >
      {preset.label}
    </button>
  ))}
</div>
```

## Verification Commands
```bash
# Check for TypeScript/ESLint errors
cd trading_lab/web && npm run lint

# Start dev server
cd trading_lab/web && npm run dev

# Visual verification at http://localhost:3847/backtests/new:
# 1. Hover over tooltip icons - verify tooltips appear
# 2. Enter invalid values - verify error messages appear
# 3. Change dates - verify duration estimate updates
# 4. Click presets - verify date fields populate
# 5. Verify submit button disabled with errors
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-form-ux.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
