import AsyncSelect from 'react-select/async'

const customStyles = {
  control: (provided, state) => ({
    ...provided,
    borderColor: state.isFocused ? 'var(--line-strong)' : 'var(--line)',
    boxShadow: state.isFocused ? '0 0 0 3px rgba(170, 90, 43, 0.18)' : 'none',
    borderRadius: '12px',
    minHeight: '44px',
    backgroundColor: 'var(--surface)',
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? 'var(--brand-dark)'
      : state.isFocused
      ? 'var(--surface-soft)'
      : 'var(--surface)',
    color: state.isSelected ? 'white' : 'var(--ink)',
    cursor: 'pointer',
  }),
  multiValue: (provided) => ({
    ...provided,
    borderRadius: '999px',
    backgroundColor: 'var(--surface-soft)',
  }),
  menu: (provided) => ({
    ...provided,
    borderRadius: '12px',
    overflow: 'hidden',
  }),
}

export default function SearchSelect({
  loadOptions,
  value,
  onChange,
  placeholder,
  isMulti = false,
  defaultOptions = true,
  noOptionsMessage = () => 'No results found',
  isClearable = true,
  ...rest
}) {
  return (
    <AsyncSelect
      cacheOptions
      defaultOptions={defaultOptions}
      isMulti={isMulti}
      isClearable={isClearable}
      value={value}
      onChange={onChange}
      loadOptions={loadOptions}
      placeholder={placeholder}
      noOptionsMessage={noOptionsMessage}
      styles={customStyles}
      {...rest}
    />
  )
}
