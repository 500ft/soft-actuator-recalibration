function v = sar_f(s, key)
%SAR_F Field of a decoded JSON object by its original key (e.g. '0.10', 'u+onset').
v = s.(matlab.lang.makeValidName(key));
end
