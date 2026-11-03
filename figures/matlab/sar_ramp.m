function C = sar_ramp(base, n, lo)
%SAR_RAMP n colours from a light tint of BASE (fraction LO of full strength) to BASE.
if nargin < 3, lo = 0.3; end
t = linspace(lo, 1, n)';
C = 1 - (1 - base) .* t;
end
