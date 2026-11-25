from django.views.generic import TemplateView
from django.http import Http404
from . import data as D
from .models import ToolUsage


def _enrich_tool(t: dict, group_map: dict) -> dict:
    g = group_map.get(t['group'], {})
    return {
        **t,
        'group_name': g.get('name', ''),
        'color': g.get('color', '#34D37B'),
        'bg': g.get('bg', 'rgba(52,211,123,0.12)'),
    }


class IndexView(TemplateView):
    """Main toolbox hub page."""
    template_name = 'tools/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        gm = {g['id']: g for g in D.GROUPS}
        tools = [_enrich_tool(t, gm) for t in D.TOOLS]
        ctx['groups'] = D.GROUPS
        ctx['tools'] = tools
        ctx['total'] = len(tools)
        return ctx


class ToolPageView(TemplateView):
    """Individual tool page."""
    template_name = 'tools/tool_page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tool_id = self.kwargs.get('tool_id')
        tool = next((t for t in D.TOOLS if t['id'] == tool_id), None)
        if not tool:
            raise Http404("Tool not found")

        # Log tool usage
        if not self.request.session.session_key:
            self.request.session.create()
        ToolUsage.objects.create(
            tool_id=tool_id,
            session_key=self.request.session.session_key or '',
        )

        gm = {g['id']: g for g in D.GROUPS}
        same_group = [t for t in D.TOOLS if t['group'] == tool['group'] and t['id'] != tool_id]
        other_group = [t for t in D.TOOLS if t['group'] != tool['group']]
        related = [_enrich_tool(r, gm) for r in (same_group + other_group)[:4]]

        # Relevant products matching group
        prods = [p for p in D.PRODUCTS if tool['group'] in p['for_groups']]
        if not prods:
            prods = D.PRODUCTS[:3]

        ctx['tool'] = _enrich_tool(tool, gm)
        ctx['related'] = related
        ctx['products'] = prods
        ctx['groups'] = D.GROUPS
        return ctx
