import { useSearchParams } from 'react-router-dom';

interface Props {
  className?: string;
}

export function PeriodoSelector({ className }: Props) {
  const [searchParams, setSearchParams] = useSearchParams();
  const periodo = searchParams.get('periodo') ?? '';

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSearchParams(
      (prev) => {
        if (e.target.value) {
          prev.set('periodo', e.target.value);
        } else {
          prev.delete('periodo');
        }
        return prev;
      },
      { replace: true },
    );
  }

  return (
    <input
      type="month"
      value={periodo}
      onChange={handleChange}
      className={className}
      aria-label="Seleccionar período"
    />
  );
}
