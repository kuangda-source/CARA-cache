"""CPU-only saved branch common/difference diagnostics, no GPU admission."""
import wc_cara_scout_mechanism_cpu_r1 as controller
controller.STAGE='cara-scout-cfg-modes-saved-r1-20261027'
controller.ANALYZER='scripts/analyze_cara_scout_cfg_modes_saved_r1.py'
if __name__=='__main__':controller.main()
