# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Thiago Bellini <hackedbellini@async.com.br>
#

"""Multicombo proxy for the kiwi framework"""

import gobject

from kiwi.datatypes import ValueUnset
from kiwi.ui.multicombo import MultiCombo
from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import gsignal, type_register


class ProxyMultiCombo(MultiCombo, ProxyWidgetMixin):

    __gtype_name__ = 'ProxyMultiCombo'

    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self, **kwargs):
        ProxyWidgetMixin.__init__(self)
        MultiCombo.__init__(self, **kwargs)

        self.connect('item-added', self._on_combo__item_added)
        self.connect('item-removed', self._on_combo__item_removed)

    #
    #  ProxyWidgetMixin
    #

    def read(self):
        return self.get_selection_data()

    def update(self, data):
        if data is ValueUnset or data is None:
            return
        self.add_selection_by_data(data)

    #
    #  Callbacks
    #

    def _on_combo__item_added(self, multicombo, item):
        self.emit('content-changed')

    def _on_combo__item_removed(self, multicombo, item):
        self.emit('content-changed')


type_register(ProxyMultiCombo)
