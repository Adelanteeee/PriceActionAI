# PriceActionAI v1.7.5 — Correction Temporal Gate
#
# Branch marker for the v1.7.5 experimental spike.
# The verified runnable offline build is maintained as the conversation artifact
# while this spike remains under visual validation. Do not merge this marker to main.
#
# Active experimental rule:
#   1 active bar  -> never an independent correction
#   2-4 active bars -> internal / pressure-drop by default
#   >=5 active bars -> eligible for existing Reference/Quality evaluation
#
# Base behavior preserved from v1.7.3:
#   RMS -> nearest actual structural leg reference
#   50/70 major-swing thresholds
#   non-destructive internal candidates
#   extreme carry-forward
#   balance disabled
#
# Runnable verified build filename:
#   price_action_ai_v1_7_5_offline_temporal_gate.py
