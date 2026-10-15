"""Strict detector-control inputs and sampling-preserving AR(1) diagnostics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.official_lc_qpo_analysis import _candidate_peaks, _simulate_ar1


def prepare_light_curves(raw: pd.DataFrame):
    required = {'mjd','flux','flux_err','Tobs_s','valid_fit','at_boundary',
                'error_reliable','low_exposure','extreme_flux'}
    if missing := required-set(raw):
        raise ValueError(f'Missing input columns: {sorted(missing)}')
    audit = raw.copy().reset_index(drop=True)
    for col in ('mjd','flux','flux_err','Tobs_s'):
        audit[col] = pd.to_numeric(audit[col], errors='coerce')
    if not np.all(np.isfinite(audit.mjd)) or not np.allclose(np.diff(audit.mjd),2):
        raise ValueError('Input must retain its complete, ordered 2-day time grid')
    reasons = {
        'invalid_fit': ~audit.valid_fit.eq(True),
        'nonfinite_flux': ~np.isfinite(audit.flux),
        'invalid_error': ~np.isfinite(audit.flux_err) | audit.flux_err.le(0),
        'invalid_exposure': ~np.isfinite(audit.Tobs_s) | audit.Tobs_s.le(0),
        'at_boundary': audit.at_boundary.eq(True),
        'error_unreliable': audit.error_reliable.eq(False),
        'low_exposure': audit.low_exposure.eq(True),
        'extreme_flux': audit.extreme_flux.eq(True),
    }
    audit['exclusion_reason'] = [';'.join(k for k,v in reasons.items() if v.iloc[i])
                                 for i in range(len(audit))]
    audit['retained'] = audit.exclusion_reason.eq('')
    observed = audit.loc[audit.retained].copy().reset_index(drop=True)
    if len(observed)<8 or observed.flux.std()==0:
        raise ValueError('Need at least eight retained, nonconstant observations')
    internal = audit.mjd.between(observed.mjd.iloc[0],observed.mjd.iloc[-1])
    grid = audit.loc[internal,['mjd']].copy().reset_index(drop=True)
    grid['flux'] = np.interp(grid.mjd,observed.mjd,observed.flux)
    grid['is_interpolated'] = ~grid.mjd.isin(observed.mjd)
    return audit,observed,grid


def adjacent_ar1(t, y):
    t,y = np.asarray(t),np.asarray(y)
    adjacent = np.isclose(np.diff(t),2,rtol=0,atol=1e-6)
    left,right = y[:-1][adjacent],y[1:][adjacent]
    if len(left)<3 or np.std(left)==0 or np.std(right)==0:
        raise ValueError('Insufficient nonconstant adjacent real pairs for AR(1)')
    return float(np.clip(np.corrcoef(left,right)[0,1],-.95,.95)),len(left)


def sample_masked_ar1(seed, mask, alpha, mean, std):
    return _simulate_ar1(len(mask),alpha,mean,std,np.random.default_rng(seed))[mask]


class CachedWWZ:
    """Cache flux-independent libwwz linear-grid terms for repeated surrogates.

    Compatibility deliberately includes libwwz's skipped first datum and
    frequency-to-frequency dvarw carry. This is an acceleration of the installed
    implementation, not a revised WWZ estimator; parity is checked before use.
    """
    def __init__(self,t,tau,freq,decay):
        self.shape=(len(tau),len(freq))
        phase=2*np.pi*np.asarray(freq)[None,:,None]*(np.asarray(t)[None,None,:]-np.asarray(tau)[:,None,None])
        w=np.exp(-decay*phase**2)
        w[w<=1e-9]=0
        w[:,:,0]=0
        cosine,sine=np.cos(phase),np.sin(phase)
        self.w=w.reshape(-1,len(t))
        self.wc=(w*cosine).reshape(-1,len(t))
        self.ws=(w*sine).reshape(-1,len(t))
        self.sumw=self.w.sum(axis=1)
        self.neff=self.sumw**2/np.maximum((self.w**2).sum(axis=1),1e-300)
        safe=np.maximum(self.sumw,1e-300)
        mat=np.zeros((len(safe),3,3))
        mat[:,0,0]=1
        mat[:,0,1]=mat[:,1,0]=self.wc.sum(axis=1)/safe
        mat[:,0,2]=mat[:,2,0]=self.ws.sum(axis=1)/safe
        mat[:,1,1]=(w*cosine**2).sum(axis=2).ravel()/safe
        mat[:,1,2]=mat[:,2,1]=(w*cosine*sine).sum(axis=2).ravel()/safe
        mat[:,2,2]=(w*sine**2).sum(axis=2).ravel()/safe
        active=self.neff>3
        self.inverse=np.zeros_like(mat)
        nonsingular=active & (np.linalg.det(mat)!=0)
        self.inverse[nonsingular]=np.linalg.inv(mat[nonsingular])
        singular=active & ~nonsingular
        if singular.any():
            self.inverse[singular]=np.linalg.pinv(mat[singular])

    def power(self,y):
        safe=np.maximum(self.sumw,1e-300)
        vec=np.column_stack((self.w@y,self.wc@y,self.ws@y))/safe[:,None]
        coef=np.einsum('nij,nj->ni',self.inverse,vec)
        model=(coef*vec).sum(axis=1)-vec[:,0]**2
        weighted_variance=(self.w@(np.asarray(y)**2)).reshape(self.shape)
        mean2=(vec[:,0]**2).reshape(self.shape)
        sums=self.sumw.reshape(self.shape)
        neff=self.neff.reshape(self.shape)
        model=model.reshape(self.shape)
        result=np.zeros(self.shape)
        carry=np.zeros(self.shape[0])
        for j in range(self.shape[1]):
            carry=carry+weighted_variance[:,j]
            active=neff[:,j]>3
            variance=np.where(sums[:,j]>.005,carry/np.maximum(sums[:,j],1e-300),0)-mean2[:,j]
            variance=np.where(variance<=0,1e-12,variance)
            carry=np.where(active,variance,carry)
            with np.errstate(divide='ignore',invalid='ignore'):
                result[:,j]=np.where(active,(neff[:,j]-3)*model[:,j]/(2*(variance-model[:,j])),0)
        result[result<1e-9]=0
        if not np.all(np.isfinite(result)):
            raise ValueError('Nonfinite cached WWZ power')
        return result


def wwz_significance(period,observed,simulated,*,alpha,span):
    period,observed=np.asarray(period),np.asarray(observed)
    q95,q99=np.percentile(simulated,[95,99],axis=0)
    refs=dict(period=period,global_wwz=observed,q95=q95,q99=q99,
              n_surrogates=len(simulated),alpha=alpha,
              period_min=float(period.min()),period_max=float(period.max()))
    sorted_period,peaks=_candidate_peaks(period,observed,period.min(),period.max())
    rows=[]
    for peak in peaks:
        p=float(sorted_period[peak])
        i=int(np.argmin(abs(period-p)))
        window=(period>=p*.9)&(period<=p*1.1)
        window_observed=float(observed[window].max())
        exceed=int((simulated[:,window].max(axis=1)>=window_observed).sum())
        global_exceed=int((simulated.max(axis=1)>=window_observed).sum())
        local_fap=(exceed+1)/(len(simulated)+1)
        global_fap=(global_exceed+1)/(len(simulated)+1)
        rows.append(dict(method='WWZ',period_days=p,cycles=span/p,ar1_alpha=alpha,
            observed_statistic=float(observed[i]),reference_95=float(q95[i]),reference_99=float(q99[i]),
            above_95=bool(observed[i]>=q95[i]),above_99=bool(observed[i]>=q99[i]),
            window_observed_statistic=window_observed,local_fap=local_fap,global_fap=global_fap,
            four_source_fap=min(1.,4*global_fap),exceed_count=exceed,global_exceed_count=global_exceed,
            n_surrogates=len(simulated),local_window_min_days=p*.9,local_window_max_days=p*1.1))
    return rows,refs
