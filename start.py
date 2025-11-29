import ipywidgets as ipw


def get_start_widget(appbase, jupbase):
    template = """
    <table style="border-collapse: collapse;">
      <tr>
        <th style="text-align:center; padding: 6px;">Density functional theory</th>
      </tr>

      <tr>
        <td valign="top" style="padding: 6px;">
          <ul>
            <li><a href="{appbase}/submit_geometry_optimization.ipynb" target="_blank">Geometry optimization</a></li>
            <li><a href="{appbase}/search.ipynb" target="_blank">Search</a></li>
          </ul>
        </td>
      </tr>
    </table>
    """

    html = template.format(appbase=appbase, jupbase=jupbase)
    return ipw.HTML(html)
