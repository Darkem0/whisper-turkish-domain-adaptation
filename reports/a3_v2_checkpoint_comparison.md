# A3_v2 checkpoint comparison

{
  "step-050": {
    "metrics": {
      "mediaspeech_clean": {
        "samples": 493,
        "normalized_wer": 0.14253943984988532,
        "normalized_cer": 0.08375106297274314,
        "raw_wer": 0.4267148516227674,
        "raw_cer": 0.14053289055796384,
        "prediction_sha256": "1b22c3c5c51e2367d82ca551f9c2189be5a44dda31132236da2b62723802a6b2"
      },
      "mediaspeech_phone": {
        "samples": 493,
        "normalized_wer": 0.15734241434429078,
        "normalized_cer": 0.09463814169986125,
        "raw_wer": 0.4412398359858225,
        "raw_cer": 0.15116395689626352,
        "prediction_sha256": "b7f1a44fb20f5d7c267f5f81a440f4073d4553d2ae42775a04f9aa44d32d0dad"
      },
      "mediaspeech_g711": {
        "samples": 493,
        "normalized_wer": 0.14712627701716588,
        "normalized_cer": 0.08732041355234302,
        "raw_wer": 0.42824379734519424,
        "raw_cer": 0.1440877230128041,
        "prediction_sha256": "822e19ac4adcb54b38e39fe9726e9b7f3459a847a92d39264f8866bc90afc852"
      },
      "cv_scripted": {
        "samples": 9650,
        "normalized_wer": 0.2353225373534938,
        "normalized_cer": 0.10411396065474585,
        "raw_wer": 0.26068666762136616,
        "raw_cer": 0.12824927968291772,
        "prediction_sha256": "671f03c99b3df4f811426edb86a1245bc1693e22850e4ecd35f592170817f814"
      },
      "fleurs": {
        "samples": 743,
        "normalized_wer": 0.07004700624181244,
        "normalized_cer": 0.021089002740378886,
        "raw_wer": 0.2769912881144991,
        "raw_cer": 0.06095495303412577,
        "prediction_sha256": "f8d77271894ba59a27e4b3d433ef4e837ed9211ad11f6fd880745eea0109d0a5"
      },
      "cv_spontaneous": {
        "samples": 11,
        "normalized_wer": 0.2360248447204969,
        "normalized_cer": 0.1602972399150743,
        "raw_wer": 0.391304347826087,
        "raw_cer": 0.18491735537190082,
        "prediction_sha256": "24e21a90c3049df693d07bfafdcd06a49f4b746e5e4183fb9f0be51437bc218b"
      },
      "tsc_exploratory": {
        "samples": 3484,
        "normalized_wer": 0.16277791351087223,
        "normalized_cer": 0.06950834388676039,
        "raw_wer": 0.38773515758612265,
        "raw_cer": 0.12350448587443827,
        "prediction_sha256": "e5dfe198622c872db53cfd87a030f603301a61f2676e6816824666f039028d50"
      }
    },
    "robustness_proxy_vs_a0": {
      "point": -0.014246994231704774,
      "lower": -0.03323802191486087,
      "upper": -0.0010200904214363732,
      "replicates": 1000,
      "seed": 20260730,
      "estimator": "weighted_media_normalized_wer_proxy_delta"
    },
    "paired_deltas": {
      "mediaspeech_clean": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_phone": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_g711": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "cv_scripted": {
        "A0": {
          "normalized_wer_delta": {
            "point": 0.07971727655005816,
            "lower": 0.047202447588256355,
            "upper": 0.11610050512617887,
            "width": 0.06889805753792251,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.048222108200931875,
            "lower": 0.030131187751755793,
            "upper": 0.06893716624687803,
            "width": 0.03880597849512223,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.0816319226983985,
            "lower": 0.04782682868012538,
            "upper": 0.11779852566848223,
            "width": 0.06997169698835684,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.044547393147056816,
            "lower": 0.026026055561013835,
            "upper": 0.0661658439917057,
            "width": 0.04013978843069187,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "fleurs": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.0328273098558989,
            "lower": -0.1071485604185189,
            "upper": 0.0093392369293073,
            "width": 0.1164877973478262,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.0014297628976528058,
            "lower": -0.015639056022744246,
            "upper": 0.011610863527469024,
            "width": 0.027249919550213268,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.10688140556368961,
            "lower": -0.2409738454679849,
            "upper": -0.0045203764229203944,
            "width": 0.2364534690450645,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.025199571071130702,
            "lower": -0.06136058719069433,
            "upper": 0.003046763718224642,
            "width": 0.06440735090891897,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "cv_spontaneous": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.024844720496894408,
            "lower": -0.1487913223140496,
            "upper": 0.027910236905020643,
            "width": 0.17670155921907024,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.040339702760084924,
            "lower": -0.19026777452903512,
            "upper": 0.018449604241686856,
            "width": 0.20871737877072197,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.0,
            "lower": -0.12100958612294584,
            "upper": 0.08163862036042487,
            "width": 0.2026482064833707,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.036093418259023353,
            "lower": -0.18395116373981202,
            "upper": 0.02536710848769688,
            "width": 0.2093182722275089,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "tsc_exploratory": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.0001832396774981676,
            "lower": -0.006639892784761339,
            "upper": 0.008589257688803137,
            "width": 0.015229150473564476,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.006599231603639997,
            "lower": -0.0033076699291930698,
            "upper": 0.02194782084998253,
            "width": 0.025255490779175598,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.011299780112387001,
            "lower": -0.043019099900881805,
            "upper": 0.009238101361602618,
            "width": 0.052257201262484426,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.0026236621193418937,
            "lower": -0.018093806744414943,
            "upper": 0.022155606775459535,
            "width": 0.040249413519874475,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      }
    }
  },
  "step-100": {
    "metrics": {
      "mediaspeech_clean": {
        "samples": 493,
        "normalized_wer": 0.14344290777677393,
        "normalized_cer": 0.08471333303495501,
        "raw_wer": 0.4271318368197929,
        "raw_cer": 0.14163611442325907,
        "prediction_sha256": "99d2debef89a58ece4a2725d951975824171ad9c9570682e49098836217a3c51"
      },
      "mediaspeech_phone": {
        "samples": 493,
        "normalized_wer": 0.15977482799360623,
        "normalized_cer": 0.09731235733786868,
        "raw_wer": 0.4430467718395997,
        "raw_cer": 0.1542396113086018,
        "prediction_sha256": "e8c336e18deaf26f68a9ba45763509284182a7c22cdf104c3b909ebcf8373a95"
      },
      "mediaspeech_g711": {
        "samples": 493,
        "normalized_wer": 0.14893321287094308,
        "normalized_cer": 0.08923376448999687,
        "raw_wer": 0.43018972826464663,
        "raw_cer": 0.14667305570723335,
        "prediction_sha256": "c48019e7b89cf172c3d171319c0983a9c6ba8a67dba150953219b5e661b057d9"
      },
      "cv_scripted": {
        "samples": 9650,
        "normalized_wer": 0.22909546389907848,
        "normalized_cer": 0.10435419626359481,
        "raw_wer": 0.26192181011026777,
        "raw_cer": 0.12792088933816495,
        "prediction_sha256": "7a4b9208ba5fb6c2ca9be4f88f13bee63fcbf755a3b297df2bcbfec23bb057d1"
      },
      "fleurs": {
        "samples": 743,
        "normalized_wer": 0.06989288741619788,
        "normalized_cer": 0.021112832122006434,
        "raw_wer": 0.2758245177349098,
        "raw_cer": 0.06069436054155858,
        "prediction_sha256": "9a1b6d36b34b043632e41a52d45b7784cb3dfccb3f521dc26a86a36cdd5202fe"
      },
      "cv_spontaneous": {
        "samples": 11,
        "normalized_wer": 0.2360248447204969,
        "normalized_cer": 0.1602972399150743,
        "raw_wer": 0.391304347826087,
        "raw_cer": 0.18491735537190082,
        "prediction_sha256": "2cd9361071958fd2f7c0a92911204d1823e7bfad47a09c634b5698098b04d1c0"
      },
      "tsc_exploratory": {
        "samples": 3484,
        "normalized_wer": 0.16488516980210116,
        "normalized_cer": 0.07126101430456923,
        "raw_wer": 0.38773515758612265,
        "raw_cer": 0.12493120234259363,
        "prediction_sha256": "5468c8c748dcdc185f490332d76825956e636c42414bfd3a45b20fb6fae97824"
      }
    },
    "robustness_proxy_vs_a0": {
      "point": -0.012735422892487316,
      "lower": -0.031618596207010206,
      "upper": 0.0008246337461745996,
      "replicates": 1000,
      "seed": 20260730,
      "estimator": "weighted_media_normalized_wer_proxy_delta"
    },
    "paired_deltas": {
      "mediaspeech_clean": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_phone": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_g711": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "cv_scripted": {
        "A0": {
          "normalized_wer_delta": {
            "point": 0.07349020309564284,
            "lower": 0.04010987102685664,
            "upper": 0.10822529645300172,
            "width": 0.06811542542614507,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.04846234380978085,
            "lower": 0.029614516812054292,
            "upper": 0.06964159220596691,
            "width": 0.04002707539391262,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.07540484924398318,
            "lower": 0.04008209144343416,
            "upper": 0.11113135982672875,
            "width": 0.07104926838329459,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.04478762875590579,
            "lower": 0.024798200866343472,
            "upper": 0.06600608634323056,
            "width": 0.041207885476887085,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "fleurs": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.03298142868151345,
            "lower": -0.10748119502560803,
            "upper": 0.009339300702045462,
            "width": 0.11682049572765349,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.0014059335160252593,
            "lower": -0.01570819385125599,
            "upper": 0.01150588404510275,
            "width": 0.02721407789635874,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.10703552438930415,
            "lower": -0.2414370045014111,
            "upper": -0.004984151807251072,
            "width": 0.23645285269416003,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.025175741689503157,
            "lower": -0.06123113020143204,
            "upper": 0.002944788531197456,
            "width": 0.0641759187326295,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "cv_spontaneous": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.024844720496894408,
            "lower": -0.1487913223140496,
            "upper": 0.027910236905020643,
            "width": 0.17670155921907024,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.040339702760084924,
            "lower": -0.19026777452903512,
            "upper": 0.018449604241686856,
            "width": 0.20871737877072197,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.0,
            "lower": -0.12100958612294584,
            "upper": 0.08163862036042487,
            "width": 0.2026482064833707,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.036093418259023353,
            "lower": -0.18395116373981202,
            "upper": 0.02536710848769688,
            "width": 0.2093182722275089,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "tsc_exploratory": {
        "A0": {
          "normalized_wer_delta": {
            "point": 0.0019240166137307598,
            "lower": -0.006448586647886046,
            "upper": 0.013618968348941487,
            "width": 0.02006755499682753,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.008351902021448839,
            "lower": -0.0034543124083968083,
            "upper": 0.024541384919085436,
            "width": 0.027995697327482243,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.009192523821158075,
            "lower": -0.04283894582750916,
            "upper": 0.011777788418116471,
            "width": 0.05461673424562563,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.004376332537150735,
            "lower": -0.016489320394670846,
            "upper": 0.024804329331230966,
            "width": 0.04129364972590181,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      }
    }
  },
  "step-150": {
    "metrics": {
      "mediaspeech_clean": {
        "samples": 493,
        "normalized_wer": 0.14775175481270414,
        "normalized_cer": 0.0893008996106163,
        "raw_wer": 0.4300507331989714,
        "raw_cer": 0.14617159031391733,
        "prediction_sha256": "e5293ee8103262347bb697e5c2da43c93208f79f323432e49b2c1d1001622881"
      },
      "mediaspeech_phone": {
        "samples": 493,
        "normalized_wer": 0.15914935019806797,
        "normalized_cer": 0.09676408718614331,
        "raw_wer": 0.4435332545694628,
        "raw_cer": 0.15415046190534562,
        "prediction_sha256": "c1f28907339922845fb304e7cd9c02229b953dddd2c23626deeaea1e8afa3446"
      },
      "mediaspeech_g711": {
        "samples": 493,
        "normalized_wer": 0.15219959691430954,
        "normalized_cer": 0.09364230407733966,
        "raw_wer": 0.4327611369796372,
        "raw_cer": 0.15101908911597223,
        "prediction_sha256": "a007ea1f4e919d4894485c76cae895eead5e3331dba11724e8dc87971f39e170"
      },
      "cv_scripted": {
        "samples": 9650,
        "normalized_wer": 0.22043482150845486,
        "normalized_cer": 0.10349112759476702,
        "raw_wer": 0.2539381354718602,
        "raw_cer": 0.12693857387212196,
        "prediction_sha256": "d7a072d350be2ee7320746d14a35aade52b35e741373662343750f70039f8fd5"
      },
      "fleurs": {
        "samples": 743,
        "normalized_wer": 0.06966170917777606,
        "normalized_cer": 0.020969855832241154,
        "raw_wer": 0.2752800248911014,
        "raw_cer": 0.06039823270909586,
        "prediction_sha256": "1515847618a76028b03c959a498c1f2894ec109cd09ca53655e1f76621bb7f18"
      },
      "cv_spontaneous": {
        "samples": 11,
        "normalized_wer": 0.2360248447204969,
        "normalized_cer": 0.1602972399150743,
        "raw_wer": 0.391304347826087,
        "raw_cer": 0.18491735537190082,
        "prediction_sha256": "84fd510e88604e9c8cbf559775a296a4b4cec0bd8a3c8e4d48e729e840d47817"
      },
      "tsc_exploratory": {
        "samples": 3484,
        "normalized_wer": 0.1588688003909113,
        "normalized_cer": 0.06485949247366987,
        "raw_wer": 0.3797336916687027,
        "raw_cer": 0.11794723820821511,
        "prediction_sha256": "a3650845af1af83814687afae05e520f08df1e898f3c93dbaa277af090b1d545"
      }
    },
    "robustness_proxy_vs_a0": {
      "point": -0.009920772812565154,
      "lower": -0.029321435762732377,
      "upper": 0.004025358034852654,
      "replicates": 1000,
      "seed": 20260730,
      "estimator": "weighted_media_normalized_wer_proxy_delta"
    },
    "paired_deltas": {
      "mediaspeech_clean": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_phone": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_g711": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "cv_scripted": {
        "A0": {
          "normalized_wer_delta": {
            "point": 0.06482956070501923,
            "lower": 0.029838717075541036,
            "upper": 0.10129779349206434,
            "width": 0.07145907641652331,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.04759927514095305,
            "lower": 0.028128975590801554,
            "upper": 0.06879865734531135,
            "width": 0.040669681754509794,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.06674420685335958,
            "lower": 0.031466948263284916,
            "upper": 0.10309460822860159,
            "width": 0.07162765996531667,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.04392456008707799,
            "lower": 0.02371329334634044,
            "upper": 0.06554244309360853,
            "width": 0.04182914974726809,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "fleurs": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.03321260691993527,
            "lower": -0.10769010533210906,
            "upper": 0.009009058276606993,
            "width": 0.11669916360871604,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.0015489098057905398,
            "lower": -0.015887587280121615,
            "upper": 0.011375996835979608,
            "width": 0.027263584116101223,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.10726670262772597,
            "lower": -0.24157056889078254,
            "upper": -0.004915737718931495,
            "width": 0.23665483117185104,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.025318717979268438,
            "lower": -0.061455885073710255,
            "upper": 0.0027614503304762227,
            "width": 0.06421733540418648,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "cv_spontaneous": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.024844720496894408,
            "lower": -0.1487913223140496,
            "upper": 0.027910236905020643,
            "width": 0.17670155921907024,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.040339702760084924,
            "lower": -0.19026777452903512,
            "upper": 0.018449604241686856,
            "width": 0.20871737877072197,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.0,
            "lower": -0.12100958612294584,
            "upper": 0.08163862036042487,
            "width": 0.2026482064833707,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.036093418259023353,
            "lower": -0.18395116373981202,
            "upper": 0.02536710848769688,
            "width": 0.2093182722275089,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "tsc_exploratory": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.004092352797459077,
            "lower": -0.008613173152503536,
            "upper": 0.002640090021119069,
            "width": 0.011253263173622605,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.001950380190549473,
            "lower": -0.005319248127667326,
            "upper": 0.014183468322422581,
            "width": 0.019502716450089906,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.015208893232347911,
            "lower": -0.04570021516324576,
            "upper": 0.003299668857260825,
            "width": 0.04899988402050658,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.0020251892937486306,
            "lower": -0.022024453032616884,
            "upper": 0.01615224865783061,
            "width": 0.0381767016904475,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      }
    }
  },
  "step-200": {
    "metrics": {
      "mediaspeech_clean": {
        "samples": 493,
        "normalized_wer": 0.1475432622141914,
        "normalized_cer": 0.08915544018260753,
        "raw_wer": 0.4283827924108694,
        "raw_cer": 0.14572584329763644,
        "prediction_sha256": "c5beb94460f4f20bd4c963a9250dddea9cca4c3c3c02d2f88035157f44ce1ff0"
      },
      "mediaspeech_phone": {
        "samples": 493,
        "normalized_wer": 0.16019181319063172,
        "normalized_cer": 0.09750257351295707,
        "raw_wer": 0.44401973729932587,
        "raw_cer": 0.154830226105174,
        "prediction_sha256": "14ada6e0c8b8c7dc0fbf6ccc5b21b3e86f652356c630011ae49de9b0f8874ade"
      },
      "mediaspeech_g711": {
        "samples": 493,
        "normalized_wer": 0.15219959691430954,
        "normalized_cer": 0.09325068254039297,
        "raw_wer": 0.4329001320453124,
        "raw_cer": 0.15067363517835453,
        "prediction_sha256": "90468fbb536dd501aa557e12d674ff893e7eefee7bb002913c364eed719c2e5f"
      },
      "cv_scripted": {
        "samples": 9650,
        "normalized_wer": 0.2193432942650085,
        "normalized_cer": 0.10020790760716436,
        "raw_wer": 0.25309680653014466,
        "raw_cer": 0.1237831709942803,
        "prediction_sha256": "ebe7f2629f5dd3e8200fa81bb041680f3b3b2e7181d13e83a836961d860ec058"
      },
      "fleurs": {
        "samples": 743,
        "normalized_wer": 0.07482468983586345,
        "normalized_cer": 0.02535446205170976,
        "raw_wer": 0.27885812072184196,
        "raw_cer": 0.06515996825509636,
        "prediction_sha256": "1aac78ce2bca14f4c5cbb17bf864aeafb07819740efce530954cc53ede6c925d"
      },
      "cv_spontaneous": {
        "samples": 11,
        "normalized_wer": 0.2360248447204969,
        "normalized_cer": 0.1602972399150743,
        "raw_wer": 0.391304347826087,
        "raw_cer": 0.18491735537190082,
        "prediction_sha256": "d1fd661765475af648dbbebe5be1ca8ca0b50988199e41022f986b6f2ae3223a"
      },
      "tsc_exploratory": {
        "samples": 3484,
        "normalized_wer": 0.16140361592963595,
        "normalized_cer": 0.06707704803278776,
        "raw_wer": 0.3818714879061813,
        "raw_cer": 0.12041059510641595,
        "prediction_sha256": "eba7a5f65c50ed2d45d7e8480626f40c6623110ea616782bfc39233f78d8955b"
      }
    },
    "robustness_proxy_vs_a0": {
      "point": -0.009764403363680589,
      "lower": -0.029154264685965436,
      "upper": 0.0047984136887232335,
      "replicates": 1000,
      "seed": 20260730,
      "estimator": "weighted_media_normalized_wer_proxy_delta"
    },
    "paired_deltas": {
      "mediaspeech_clean": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_phone": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "mediaspeech_g711": {
        "A0": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        },
        "A2": {
          "status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"
        }
      },
      "cv_scripted": {
        "A0": {
          "normalized_wer_delta": {
            "point": 0.06373803346157288,
            "lower": 0.03002060613184696,
            "upper": 0.09906747938240139,
            "width": 0.06904687325055443,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.044316055153350395,
            "lower": 0.025930851460222407,
            "upper": 0.06383968596173768,
            "width": 0.037908834501515276,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.06565267960991321,
            "lower": 0.030414084287867935,
            "upper": 0.10317366640707352,
            "width": 0.07275958211920559,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.040641340099475336,
            "lower": 0.020809592724236613,
            "upper": 0.06164692076433652,
            "width": 0.0408373280400999,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "fleurs": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.028049626261847885,
            "lower": -0.10708403031699491,
            "upper": 0.019356480054527732,
            "width": 0.12644051037152265,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.002835696413678065,
            "lower": -0.012012763309390143,
            "upper": 0.019856865304650192,
            "width": 0.031869628614040336,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.10210372196963859,
            "lower": -0.23393457045165075,
            "upper": 0.0017871148238415226,
            "width": 0.23572168527549228,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.020934111759799832,
            "lower": -0.05770871769255451,
            "upper": 0.009983996678034884,
            "width": 0.0676927143705894,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "cv_spontaneous": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.024844720496894408,
            "lower": -0.1487913223140496,
            "upper": 0.027910236905020643,
            "width": 0.17670155921907024,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.040339702760084924,
            "lower": -0.19026777452903512,
            "upper": 0.018449604241686856,
            "width": 0.20871737877072197,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": 0.0,
            "lower": -0.12100958612294584,
            "upper": 0.08163862036042487,
            "width": 0.2026482064833707,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": -0.036093418259023353,
            "lower": -0.18395116373981202,
            "upper": 0.02536710848769688,
            "width": 0.2093182722275089,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      },
      "tsc_exploratory": {
        "A0": {
          "normalized_wer_delta": {
            "point": -0.0015575372587344246,
            "lower": -0.007956132661535522,
            "upper": 0.007322667177976919,
            "width": 0.015278799839512441,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.004167935749667367,
            "lower": -0.004789189438510897,
            "upper": 0.01764965799001294,
            "width": 0.022438847428523836,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        },
        "A2": {
          "normalized_wer_delta": {
            "point": -0.012674077693623258,
            "lower": -0.04511705035868047,
            "upper": 0.006892791766890965,
            "width": 0.052009842125571436,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_wer_delta"
          },
          "normalized_cer_delta": {
            "point": 0.00019236626536926307,
            "lower": -0.019973104090198816,
            "upper": 0.017722120172121335,
            "width": 0.03769522426232015,
            "replicates": 1000,
            "seed": 20260730,
            "resampling": "paired_stable_id_with_replacement",
            "estimator": "paired_corpus_normalized_cer_delta"
          }
        }
      }
    }
  }
}
