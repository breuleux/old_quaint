
from colonel.tools.svg import CSS

pp_css = CSS({
        'span': {'vertical-align': 'middle'},

        # '.apply > span': {
        #     'color': '#0f0',
        #     'vertical-align': 'top'
        #     },

        '.symbol': {'color': '#fff',
                    # 'padding-left': '5px',
                    # 'padding-right': '5px',
                    # 'display': 'inline-block',
                    },
        '.quoted-symbol': {'color': '#0f0',
                           # 'vertical-align': 'top',
                           # 'vertical-align': 'middle'
                           },
        '.value': {'color': '#88f',
                   # 'vertical-align': 'middle'
                   },
        '.void': {'color': '#888',
                  # 'vertical-align': 'middle'
                  },

        '.syntax': {'display': 'inline-block',
                    'border': '5px solid #080',
                    # 'vertical-align': 'middle'
                    },
        '.quote': {'display': 'inline-block',
                   'border': '3px dashed #080',
                   },
        
        '.apply': {'display': 'inline-block',
                   'border-bottom': '2px solid #f88',
                   'vertical-align': 'bottom',
                   'padding-bottom': '5px'},
        '.apply-sep': {'color': '#f88',
                       'padding': '0px'},

        # '.apply': {'display': 'inline-block',
        #            'border-top': '2px solid #f88',
        #            'vertical-align': 'top',
        #            'padding-top': '5px'},
        # '.apply-sep': {'color': '#f88',
        #                'padding': '0px'},

        '.begin': {'display': 'inline-block',
                   # 'vertical-align': 'middle',
                   'border': '1px dotted #008'
                   },
        '.begin-inner': {'display': 'table-row'},
        '.begin-cell': {'display': 'table-cell',
                        'border-left': '1px solid #008',
                        'padding': '5px'},

        '.table': {'display': 'inline-block',
                   # 'vertical-align': 'middle',
                   'border': '2px solid #800'},
        '.table-inner': {'display': 'table-row'},
        '.table-cell': {'display': 'table-cell',
                        'border-left': '1px solid #800',
                        'padding': '5px'},

        '.if': {'display': 'inline-block',
                # 'vertical-align': 'middle',
                'border': '3px solid #ff0',
                'padding': '5px'},
        '.if-cond': {'display': 'inline-block',
                     # 'vertical-align': 'middle',
                     'border': '1px solid #880',
                     'padding': '5px'},
        '.if-true': {'display': 'inline-block',
                     # 'vertical-align': 'middle',
                     'padding-right': '10px',
                     'border-right': '1px dashed #880'
                     },
        '.if-false': {'display': 'inline-block',
                      # 'vertical-align': 'middle',

                      # 'padding-left': '10px',
                      # 'border-left': '1px dashed #880'
                      },
        # '.if-sep': {'display': 'inline',
        #             'border': '1px dashed #880'},

        # '.lambda': {'display': 'inline-block',
        #             'border-bottom': '2px solid #88f',
        #             'vertical-align': 'bottom',
        #             'padding-bottom': '5px'},

        '.lambda': {'display': 'inline-block',
                    # 'font-size': '12'
                    'border': '1px dashed #88f',
                    'padding': '5px',
                    # 'vertical-align': 'middle'
                    },
        '.lambda-chr': {'color': '#88f',
                        'display': 'inline-block',
                        # 'vertical-align': 'middle'
                        # 'font-size': '12'
                        },
        '.lambda-param': {'color': '#ff0',
                          'display': 'inline-block',
                          'vertical-align': 'middle'
                          },
        '.lambda-sep': {'color': '#88f',
                        'display': 'none',
                        # 'display': 'inline-block',
                        },
        '.lambda-body': {'vertical-align': 'middle',
                         'display': 'inline-block',
                         }
        # '.lambda-sep': {'border': '1px solid #ff0',
        #                 'margin-right': '10px'},

        })




svg_css = CSS({

        '.port': {'stroke-width': 2},

        '.port-VOID': {'fill': 'black'},
        '.port-NOTAG': {'fill': 'black'},
        '.port-AVAIL': {'fill': 'yellow'},
        '.port-REQ': {'fill': 'cyan'},

        '.port-send-VOID': {'stroke': 'black'},
        '.port-send-NOTAG': {'stroke': 'black'},
        '.port-send-AVAIL': {'stroke': 'yellow'},
        '.port-send-REQ': {'stroke': 'cyan'},

        '.trapezoid-gate': {'stroke-width': 5,
                            'stroke': 'black',
                            'fill': '#ff0'},

        '.circuit-gate': {'stroke-width': 5,
                          'stroke': 'black',
                          'fill': '#cccccc'},

        '.rect-gate': {'stroke-width': 5,
                       'stroke': 'black',
                       'fill': '#88f'},

        '.title': {'font-family': 'monospace',
                   'font-weight': 'bold'},

        '.port-label': {'font-family': 'monospace',
                        'fill': 'black'},

        '.link': {'stroke-width': 5,
                  'stroke': 'black'},

        '.active-link': {'stroke-width': 8,
                         'stroke': 'black'},

        '.link-label': {'font-family': 'monospace'},

        '.link-label-box': {'fill': 'yellow',
                            'stroke': 'black'},

        })

