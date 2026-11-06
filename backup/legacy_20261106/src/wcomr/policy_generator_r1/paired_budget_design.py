"""Frozen mean-budget statistic for future confirmation, not a runtime gate."""
import math
import random

ABSOLUTE_SECONDS = 257.7712338712067
NATIVE_FRACTION = .8


def paired_budget(rows, *, resamples=20000, seed=20261025):
    """Each row is one prompt with equally many matched candidate/Native clocks.

    Average repeats within prompt, then bootstrap paired prompt clusters. This
    estimates a mean constraint; it neither proves an SLA nor adds prompt count
    through repeats. Caller must supply the complete preregistered cohort.
    """
    if len(rows) < 2 or len({r['prompt'] for r in rows}) != len(rows):
        raise ValueError('At least two distinct complete prompt clusters required')
    if type(resamples) is not int or resamples < 100:
        raise ValueError('Insufficient bootstrap resamples')
    values = []
    for r in rows:
        c, n = r['candidate'], r['native']
        if not c or len(c) != len(n) or any(not math.isfinite(x) or x <= 0 for x in c+n):
            raise ValueError('Positive finite paired complete-request clocks required')
        values.append((sum(c)/len(c), sum(n)/len(n)))

    def estimate(v):
        c = sum(x[0] for x in v)/len(v)
        n = sum(x[1] for x in v)/len(v)
        return c, n, max(c/ABSOLUTE_SECONDS, c/(NATIVE_FRACTION*n))

    c, n, statistic = estimate(values)
    rng = random.Random(seed)
    boot = sorted(estimate([values[rng.randrange(len(values))] for _ in values])[2]
                  for _ in range(resamples))
    upper = boot[math.ceil(.95*(resamples-1))]
    return dict(prompts=len(values), mean_candidate=c, mean_native=n,
                ratio_of_means=c/n, paired_difference_seconds=c-n,
                mean_of_prompt_ratios=sum(x/y for x, y in values)/len(values),
                V=statistic, V_upper95=upper, point_pass=statistic <= 1,
                mean_budget_statistical_support=upper <= 1,
                deployment_accepted=False, resamples=resamples, seed=seed,
                method='PROMPT_PAIRED_PERCENTILE_HIGHER_REPEATS_AVERAGED_FIRST')
