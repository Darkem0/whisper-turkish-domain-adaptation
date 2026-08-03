# MediaSpeech stable-ID audit

{
  "canonical_mapping": "sample_id is canonical: media-<stable_source_id>--<degradation>",
  "variants": {
    "step-050": {
      "exact_sample_id_match_with_A0": true,
      "a0_missing": 0,
      "a2_missing": 0,
      "duplicate_or_missing": false,
      "paired_ci": {
        "clean": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.020015289457224267,
              "lower": -0.05747306166136708,
              "upper": 0.00370088065259266,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.012162646018887347,
              "lower": -0.03689888900165103,
              "upper": 0.006618461744725165,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.004308847035930224,
              "lower": -0.005762311130611291,
              "upper": 0.015371972244855953,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.00695967417088126,
              "lower": -0.003830487040678424,
              "upper": 0.01821386860130853,
              "replicates": 1000
            }
          }
        },
        "phone_8khz": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.018347348669122247,
              "lower": -0.03286166855680287,
              "upper": -0.0048704385465655154,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.016705455847469006,
              "lower": -0.03161781219427802,
              "upper": -0.002156617494054434,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": -0.013482521370491347,
              "lower": -0.029154477090349486,
              "upper": 0.0008307456459600671,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.010663294991720002,
              "lower": -0.026571086937845705,
              "upper": 0.0046129531744786055,
              "replicates": 1000
            }
          }
        },
        "g711_mulaw": {
          "A0": {
            "normalized_wer_delta": {
              "point": 0.0013899506567516854,
              "lower": -0.008763718845956892,
              "upper": 0.011499885818837378,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.0037036208208387415,
              "lower": -0.007265481492424501,
              "upper": 0.01406058328242137,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.008200708874834943,
              "lower": -0.0030029012644104307,
              "upper": 0.020132611069161855,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.010193349147383969,
              "lower": -0.0014328087515762637,
              "upper": 0.021865351153675546,
              "replicates": 1000
            }
          }
        }
      }
    },
    "step-100": {
      "exact_sample_id_match_with_A0": true,
      "a0_missing": 0,
      "a2_missing": 0,
      "duplicate_or_missing": false,
      "paired_ci": {
        "clean": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.019111821530335672,
              "lower": -0.05649366643812929,
              "upper": 0.0048489127160909595,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.011200375956675468,
              "lower": -0.03616702253602657,
              "upper": 0.007913954649266473,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.00521231496281882,
              "lower": -0.005022111968323735,
              "upper": 0.016205403559806247,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.007921944233093139,
              "lower": -0.003229437315302323,
              "upper": 0.019151474215045722,
              "replicates": 1000
            }
          }
        },
        "phone_8khz": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.015914935019806797,
              "lower": -0.03280356422252111,
              "upper": 8.636771920119277e-06,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.014031240209461577,
              "lower": -0.030815685520148746,
              "upper": 0.003578370317419533,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": -0.011050107721175898,
              "lower": -0.027829397162827913,
              "upper": 0.004740145347737457,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.007989079353712573,
              "lower": -0.02479516089364925,
              "upper": 0.009799300556236805,
              "replicates": 1000
            }
          }
        },
        "g711_mulaw": {
          "A0": {
            "normalized_wer_delta": {
              "point": 0.003196886510528876,
              "lower": -0.007029004134134739,
              "upper": 0.013309266051589582,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.005616971758492593,
              "lower": -0.0051566808731862545,
              "upper": 0.016261397032190733,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.010007644728612134,
              "lower": -0.0014146275707030995,
              "upper": 0.021687904447954987,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.01210670008503782,
              "lower": 0.00041231738710017927,
              "upper": 0.02421289655871598,
              "replicates": 1000
            }
          }
        }
      }
    },
    "step-150": {
      "exact_sample_id_match_with_A0": true,
      "a0_missing": 0,
      "a2_missing": 0,
      "duplicate_or_missing": false,
      "paired_ci": {
        "clean": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.014802974494405449,
              "lower": -0.05403503295180164,
              "upper": 0.01164228307727936,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.006612809381014188,
              "lower": -0.0327492553716428,
              "upper": 0.013392300876933638,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.009521161998749044,
              "lower": -0.001545194041306301,
              "upper": 0.023067483432477054,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.012509510808754419,
              "lower": -3.5071916075473796e-05,
              "upper": 0.026125417442903986,
              "replicates": 1000
            }
          }
        },
        "phone_8khz": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.016540412815345056,
              "lower": -0.033445619283053105,
              "upper": -0.0006932416362631777,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.014579510361186949,
              "lower": -0.031163794600979743,
              "upper": 0.0030754638186617457,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": -0.011675585516714156,
              "lower": -0.028385351838213696,
              "upper": 0.00397242395133939,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.008537349505437945,
              "lower": -0.025256647626389687,
              "upper": 0.008997526828137089,
              "replicates": 1000
            }
          }
        },
        "g711_mulaw": {
          "A0": {
            "normalized_wer_delta": {
              "point": 0.006463270553895337,
              "lower": -0.005687729420781899,
              "upper": 0.0211031337323606,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.010025511345835385,
              "lower": -0.003875647341076374,
              "upper": 0.025064245551000154,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.013274028771978594,
              "lower": 0.0002105756031167242,
              "upper": 0.02909591760511385,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.01651523967238061,
              "lower": 0.0009651892132876246,
              "upper": 0.03245153124503004,
              "replicates": 1000
            }
          }
        }
      }
    },
    "step-200": {
      "exact_sample_id_match_with_A0": true,
      "a0_missing": 0,
      "a2_missing": 0,
      "duplicate_or_missing": false,
      "paired_ci": {
        "clean": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.015011467092918201,
              "lower": -0.05403666712135662,
              "upper": 0.011395915819169431,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.00675826880902296,
              "lower": -0.03271291779355548,
              "upper": 0.013801512781073805,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.009312669400236291,
              "lower": -0.0020165056523151876,
              "upper": 0.02285164434392257,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.012364051380745648,
              "lower": -0.0003487977145851701,
              "upper": 0.026435727060621417,
              "replicates": 1000
            }
          }
        },
        "phone_8khz": {
          "A0": {
            "normalized_wer_delta": {
              "point": -0.015497949822781291,
              "lower": -0.03256610217398149,
              "upper": -0.00020353489666690336,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.013841024034373182,
              "lower": -0.03041650197696134,
              "upper": 0.003239157769489274,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": -0.010633122524150393,
              "lower": -0.027558367127205302,
              "upper": 0.005187693361918649,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": -0.007798863178624178,
              "lower": -0.0246476464945607,
              "upper": 0.008904443093037229,
              "replicates": 1000
            }
          }
        },
        "g711_mulaw": {
          "A0": {
            "normalized_wer_delta": {
              "point": 0.006463270553895337,
              "lower": -0.005444671118780257,
              "upper": 0.0210942533946238,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.00963388980888869,
              "lower": -0.004036144626677633,
              "upper": 0.024867177698725033,
              "replicates": 1000
            }
          },
          "A2": {
            "normalized_wer_delta": {
              "point": 0.013274028771978594,
              "lower": 0.0002733186667787186,
              "upper": 0.029418140923051568,
              "replicates": 1000
            },
            "normalized_cer_delta": {
              "point": 0.016123618135433917,
              "lower": 0.0007609694810919138,
              "upper": 0.03223606043356613,
              "replicates": 1000
            }
          }
        }
      }
    }
  },
  "status": "PASSED_DETERMINISTIC_MAPPING",
  "unavailable_reason": "Earlier split-vs-combined comparison used per-variant A3 files against unsplit A0/A2 MediaSpeech files; this was a comparison-layout mismatch, not a data identity mismatch."
}
